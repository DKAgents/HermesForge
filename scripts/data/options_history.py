"""options_history.py — HermesForge US-231: Deribit options-history store.

Backfill store for the variance-risk-premium (VRP) backtest (HYP-30). Sourced
ENTIRELY from the free, no-auth Deribit public REST surface:

  * ``history.deribit.com`` — expired BTC/ETH option instrument catalogue +
    their trade history. Every trade carries THREE Deribit-quoted fields we
    record verbatim (never fabricated, never Black-Scholes-inverted):
      ``price``        — the actual traded premium
      ``mark_price``   — Deribit's mark for that option (the fair premium)
      ``iv``           — Deribit's mark_iv (%, the options' implied vol)
      ``index_price``  — the underlying index (spot) at trade time
  * ``www.deribit.com`` — DVOL (vol-index level) via ``get_volatility_index_data``
    (fits into ``iv_store.dvol_index``), plus the synthetic "realized" series is
    COMPUTED from the reconstructed underlying index closes (std of log-returns),
    not read from a paid feed.

Tables (all WITHOUT ROWID, PK-dedup safe — a second run inserts 0 rows):

  * ``underlying_daily`` — (currency, day) -> Deribit index close (day's last
    observed ``index_price``). The basis for realized-vol computation.
  * ``options_atm_straddle`` — (currency, expiry, day) -> the ATM-straddle
    reconstruction: call+put ``mark_price`` at the nearest-ATM strike, their
    average mark_iv, the underlying, and dte-to-expiry.
  * ``realized_vol_daily`` — (currency, day) -> annualized realized vol (30d
    window over ``underlying_daily``) + the DVOL daily close.
  * ``expiry_state`` — (currency, expiry) ingest checkpoint for resumability.

Store location: ~/.hermes/market_data/options_history/options_history.db

Import direction (one-way, acyclic):
  ingest_deribit_options_history.py -> options_history.py (+ iv_store for DVOL)
"""

from __future__ import annotations

import sqlite3
import pathlib

import pandas as pd

STORE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "options_history"
DB_NAME = "options_history.db"

PRAGMAS = (
    "PRAGMA journal_mode=WAL;",
    "PRAGMA synchronous=NORMAL;",
    "PRAGMA foreign_keys=ON;",
)

# The only provenance label a premium carries here. mark_price / mark_iv are
# quoted DIRECTLY by Deribit — no Black-Scholes inversion is performed, so there
# is no BS-inversion to flag; instead we flag the rare "iv missing/0" case.
MARK_SOURCE = "deribit_mark"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS underlying_daily (
    currency  TEXT    NOT NULL,   -- 'BTC' | 'ETH'
    day       INTEGER NOT NULL,   -- UTC day start, ms
    close     REAL,               -- Deribit index close (last index_price of day)
    PRIMARY KEY (currency, day)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS options_atm_straddle (
    currency  TEXT    NOT NULL,   -- 'BTC' | 'ETH'
    expiry    INTEGER NOT NULL,   -- expiration_timestamp ms
    day       INTEGER NOT NULL,   -- UTC day start, ms (snapshot bucket)
    snap_ts   INTEGER NOT NULL,   -- last trade ts of the day (provenance)
    dte       REAL,               -- (expiry - snap_ts) / 86400000
    underlying REAL,              -- Deribit index_price used for ATM selection
    strike    REAL,               -- nearest-ATM strike (USD)
    call_premium REAL,            -- Deribit mark_price of the ATM call (BTC/ETH per contract)
    put_premium  REAL,            -- Deribit mark_price of the ATM put (BTC/ETH per contract)
    atm_straddle_premium REAL,    -- call_premium + put_premium (BTC/ETH per contract)
    atm_iv    REAL,               -- 0.5*(call mark_iv + put mark_iv), %; NULL if iv missing/0
    iv_source TEXT,               -- 'deribit_mark' when mark_iv present, else NULL
    PRIMARY KEY (currency, expiry, day)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_atm_day ON options_atm_straddle (currency, day);

CREATE TABLE IF NOT EXISTS realized_vol_daily (
    currency     TEXT    NOT NULL,
    day          INTEGER NOT NULL,
    realized_vol REAL,             -- annualized DECIMAL (0.42 = 42%), 30d window
    dvol         REAL,             -- DVOL daily close, % (NULL before ~2021-05)
    PRIMARY KEY (currency, day)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS day_state (
    currency TEXT    NOT NULL,
    day      INTEGER NOT NULL,
    done     INTEGER NOT NULL,   -- 0/1
    PRIMARY KEY (currency, day)
) WITHOUT ROWID;
"""


def db_path() -> pathlib.Path:
    return STORE_DIR / DB_NAME


def open_store() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    for pragma in PRAGMAS:
        conn.execute(pragma)
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def _f(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def append_underlying(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """rows = [{currency, day, close}]. INSERT OR IGNORE keyed (currency, day)."""
    if not rows:
        return 0
    tuples = [(str(r["currency"]), int(r["day"]), _f(r.get("close"))) for r in rows]
    cur = conn.executemany(
        "INSERT OR IGNORE INTO underlying_daily (currency, day, close) VALUES (?,?,?)",
        tuples)
    conn.commit()
    return cur.rowcount if cur.rowcount is not None else 0


def append_atm_straddle(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """rows = [{currency, expiry, day, snap_ts, dte, underlying, strike,
    call_premium, put_premium, atm_straddle_premium, atm_iv, iv_source}].
    INSERT OR IGNORE keyed (currency, expiry, day)."""
    if not rows:
        return 0
    tuples = [
        (str(r["currency"]), int(r["expiry"]), int(r["day"]), int(r["snap_ts"]),
         _f(r.get("dte")), _f(r.get("underlying")), _f(r.get("strike")),
         _f(r.get("call_premium")), _f(r.get("put_premium")),
         _f(r.get("atm_straddle_premium")), _f(r.get("atm_iv")),
         r.get("iv_source"))
        for r in rows
    ]
    cur = conn.executemany(
        "INSERT OR IGNORE INTO options_atm_straddle "
        "(currency, expiry, day, snap_ts, dte, underlying, strike, call_premium, "
        " put_premium, atm_straddle_premium, atm_iv, iv_source) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", tuples)
    conn.commit()
    return cur.rowcount if cur.rowcount is not None else 0


def append_realized_vol(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """rows = [{currency, day, realized_vol, dvol}]. INSERT OR IGNORE keyed
    (currency, day)."""
    if not rows:
        return 0
    tuples = [(str(r["currency"]), int(r["day"]), _f(r.get("realized_vol")),
               _f(r.get("dvol"))) for r in rows]
    cur = conn.executemany(
        "INSERT OR IGNORE INTO realized_vol_daily (currency, day, realized_vol, dvol) "
        "VALUES (?,?,?,?)", tuples)
    conn.commit()
    return cur.rowcount if cur.rowcount is not None else 0


def mark_day_done(conn: sqlite3.Connection, currency: str, day: int) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO day_state (currency, day, done) VALUES (?,?,1)",
        (str(currency), int(day)))
    conn.commit()


def day_done(conn: sqlite3.Connection, currency: str, day: int) -> bool:
    row = conn.execute(
        "SELECT done FROM day_state WHERE currency=? AND day=?",
        (str(currency), int(day))).fetchone()
    return bool(row and row[0])


def done_days(conn: sqlite3.Connection, currency: str) -> set[int]:
    rows = conn.execute(
        "SELECT day FROM day_state WHERE currency=? AND done=1",
        (str(currency),)).fetchall()
    return {r[0] for r in rows}


# ── read API (HYP-30 backtester facing) ──────────────────────────────────────
def read_atm_straddle(currency: str, start_ts: int | None = None,
                      end_ts: int | None = None) -> pd.DataFrame:
    """DataFrame per (expiry, day): dte, underlying, strike, call/put premium,
    atm_straddle_premium, atm_iv. Ascending by day."""
    cols = ("currency, expiry, day, snap_ts, dte, underlying, strike, "
            "call_premium, put_premium, atm_straddle_premium, atm_iv, iv_source")
    conn = open_store()
    try:
        where = ["currency = ?"]
        params: list = [currency]
        if start_ts is not None:
            where.append("day >= ?")
            params.append(int(start_ts))
        if end_ts is not None:
            where.append("day < ?")
            params.append(int(end_ts))
        sql = ("SELECT " + cols + " FROM options_atm_straddle WHERE "
               + " AND ".join(where) + " ORDER BY day ASC, expiry ASC")
        df = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()
    return df


def read_underlying(currency: str) -> pd.DataFrame:
    """Daily underlying index close DataFrame[day, close] ascending."""
    conn = open_store()
    try:
        df = pd.read_sql_query(
            "SELECT day, close FROM underlying_daily WHERE currency=? "
            "ORDER BY day ASC", conn, params=[currency])
    finally:
        conn.close()
    return df


def read_realized_vol(currency: str) -> pd.DataFrame:
    conn = open_store()
    try:
        df = pd.read_sql_query(
            "SELECT day, realized_vol, dvol FROM realized_vol_daily "
            "WHERE currency=? ORDER BY day ASC", conn, params=[currency])
    finally:
        conn.close()
    return df


def coverage(conn: sqlite3.Connection, table: str, currency: str,
             day_col: str = "day") -> dict:
    row = conn.execute(
        f"SELECT MIN({day_col}), MAX({day_col}), COUNT(*) FROM {table} "
        f"WHERE currency=?", (currency,)).fetchone()
    return {"currency": currency, "min": row[0], "max": row[1], "n": row[2]}
