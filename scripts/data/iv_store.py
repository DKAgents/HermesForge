"""iv_store.py — HermesForge US-187: options implied-volatility surface store.

One store, two disjoint sub-feeds plus the crypto vol-index level:

  * ``dvol_index``     — Deribit DVOL (crypto vol-index level, unit %). This is
                         the vol-of-vol LEVEL that gates the US-181 timing signal
                         ("is realized vol itself low/high?").
  * ``crypto_atm_iv``  — Deribit BTC/ETH ATM IV term structure (per expiry, DTE,
                         average call+put mark_iv). mark_iv is quoted DIRECTLY by
                         Deribit (no Black-Scholes solve).
  * ``equity_atm_iv``  — yfinance impliedVolatility per ticker (ATM strike at the
                         target DTE), daily. IV RANK is derived at READ from the
                         252-snapshot window, never stored as a row.

Equities read the ``impliedVolatility`` column yfinance already returns (IBKR
sourced) — NO Black-Scholes solve (§2.3). Empty/temporarily-unavailable chains
are skipped, never fabricated.

Store location: ~/.hermes/market_data/iv_surface/iv_surface.db

Import direction is one-way and acyclic:
  ingest_deribit_iv.py -> iv_store.py                      [crypto]
  ingest_equity_iv.py  -> iv_store.py + universe(equity)   [equity]
"""

from __future__ import annotations

import sqlite3
import pathlib

import pandas as pd

STORE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "iv_surface"
DB_NAME = "iv_surface.db"

PRAGMAS = (
    "PRAGMA journal_mode=WAL;",
    "PRAGMA synchronous=NORMAL;",
    "PRAGMA foreign_keys=ON;",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS dvol_index (
    currency  TEXT    NOT NULL,   -- 'BTC' | 'ETH'
    ts        INTEGER NOT NULL,   -- Deribit candle ts, ms
    open      REAL, high REAL, low REAL, close REAL,
    PRIMARY KEY (currency, ts)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS crypto_atm_iv (
    currency  TEXT    NOT NULL,   -- 'BTC' | 'ETH'
    ts        INTEGER NOT NULL,   -- snapshot time, ms
    expiry    INTEGER NOT NULL,   -- expiration_timestamp ms
    dte       REAL    NOT NULL,
    atm_iv    REAL    NOT NULL,   -- % (e.g. 38.0)
    spot      REAL,
    PRIMARY KEY (currency, expiry, ts)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_crypto_atm_iv_ts ON crypto_atm_iv (currency, ts);

CREATE TABLE IF NOT EXISTS equity_atm_iv (
    ticker    TEXT    NOT NULL,
    ts        INTEGER NOT NULL,   -- snapshot time, ms (day-bucketed)
    atm_iv    REAL    NOT NULL,   -- % ; NULL permitted if chain empty (don't fabricate)
    spot      REAL,
    expiry    TEXT,               -- chosen expiry date string (provenance)
    PRIMARY KEY (ticker, ts)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_equity_atm_iv_ts ON equity_atm_iv (ticker, ts);

CREATE TABLE IF NOT EXISTS ingest_state (
    feed     TEXT    NOT NULL,    -- 'dvol' | 'crypto_atm' | 'equity_atm'
    key      TEXT    NOT NULL,    -- currency (BTC/ETH) or ticker
    last_ts  INTEGER NOT NULL,
    last_run TEXT    NOT NULL,
    PRIMARY KEY (feed, key)
) WITHOUT ROWID;
"""


def db_path() -> pathlib.Path:
    """STORE_DIR / DB_NAME."""
    return STORE_DIR / DB_NAME


def open_store() -> sqlite3.Connection:
    """Open (create if absent) the IV DB; apply PRAGMAs; run schema DDL
    idempotently. Returns a WAL-mode connection."""
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    for pragma in PRAGMAS:
        conn.execute(pragma)
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def _append(conn: sqlite3.Connection, sql: str, tuples: list) -> int:
    """Shared INSERT OR IGNORE + atomic commit. Returns new-row count."""
    if not tuples:
        return 0
    try:
        cur = conn.executemany(sql, tuples)
        conn.commit()
        return cur.rowcount if cur.rowcount is not None else 0
    except Exception:
        conn.rollback()
        raise


def append_dvol(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """rows = [{currency, ts, open, high, low, close}]. INSERT OR IGNORE keyed
    (currency, ts)."""
    tuples = [(str(r["currency"]), int(r["ts"]),
               _f(r.get("open")), _f(r.get("high")), _f(r.get("low")),
               _f(r.get("close"))) for r in rows]
    return _append(conn, "INSERT OR IGNORE INTO dvol_index "
                   "(currency, ts, open, high, low, close) VALUES (?,?,?,?,?,?)",
                   tuples)


def append_crypto_atm_iv(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """rows = [{currency, ts, expiry, dte, atm_iv, spot}]. Keyed
    (currency, expiry, ts)."""
    tuples = [(str(r["currency"]), int(r["ts"]), int(r["expiry"]),
               float(r["dte"]), float(r["atm_iv"]), _f(r.get("spot")))
              for r in rows]
    return _append(conn, "INSERT OR IGNORE INTO crypto_atm_iv "
                   "(currency, ts, expiry, dte, atm_iv, spot) "
                   "VALUES (?,?,?,?,?,?)", tuples)


def append_equity_atm_iv(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """rows = [{ticker, ts, atm_iv, spot, expiry}]. Keyed (ticker, ts)."""
    tuples = [(str(r["ticker"]), int(r["ts"]), float(r["atm_iv"]),
               _f(r.get("spot")), r.get("expiry")) for r in rows]
    return _append(conn, "INSERT OR IGNORE INTO equity_atm_iv "
                   "(ticker, ts, atm_iv, spot, expiry) VALUES (?,?,?,?,?)",
                   tuples)


def _f(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def upsert_state(conn: sqlite3.Connection, feed: str, key: str, last_ts: int,
                 last_run: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO ingest_state (feed, key, last_ts, last_run) "
        "VALUES (?,?,?,?)",
        (feed, key, int(last_ts), last_run),
    )
    conn.commit()


def last_ts(conn: sqlite3.Connection, feed: str, key: str) -> int | None:
    row = conn.execute(
        "SELECT last_ts FROM ingest_state WHERE feed=? AND key=?", (feed, key)
    ).fetchone()
    return row[0] if row and row[0] is not None else None


def coverage(conn: sqlite3.Connection, table: str, key_col: str,
             key: str) -> dict:
    row = conn.execute(
        f"SELECT MIN(ts), MAX(ts), COUNT(*) FROM {table} WHERE {key_col}=?",
        (key,),
    ).fetchone()
    return {"key": key, "min_ts": row[0], "max_ts": row[1], "n": row[2]}


def _read(columns: str, table: str, key_col: str, key: str,
          start_ts: int | None, end_ts: int | None) -> pd.DataFrame:
    where = [f"{key_col} = ?"]
    params: list = [key]
    if start_ts is not None:
        where.append("ts >= ?")
        params.append(int(start_ts))
    if end_ts is not None:
        where.append("ts < ?")
        params.append(int(end_ts))
    sql = (f"SELECT {columns} FROM {table} WHERE " + " AND ".join(where)
           + " ORDER BY ts ASC")
    conn = open_store()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()
    return df.reset_index(drop=True)


def read_dvol(currency: str, start_ts: int | None = None,
              end_ts: int | None = None) -> pd.DataFrame:
    """DataFrame[ts, open, high, low, close] ascending."""
    df = _read("ts, open, high, low, close", "dvol_index", "currency",
               currency, start_ts, end_ts)
    if df.empty:
        return pd.DataFrame(columns=["ts", "open", "high", "low", "close"])
    return df


def read_crypto_atm_iv(currency: str, start_ts: int | None = None,
                       end_ts: int | None = None) -> pd.DataFrame:
    """DataFrame[ts, expiry, dte, atm_iv, spot] ascending in ts."""
    df = _read("ts, expiry, dte, atm_iv, spot", "crypto_atm_iv", "currency",
               currency, start_ts, end_ts)
    if df.empty:
        return pd.DataFrame(columns=["ts", "expiry", "dte", "atm_iv", "spot"])
    return df


def read_equity_atm_iv(ticker: str, start_ts: int | None = None,
                       end_ts: int | None = None) -> pd.DataFrame:
    """DataFrame[ts, atm_iv, spot, expiry] ascending."""
    df = _read("ts, atm_iv, spot, expiry", "equity_atm_iv", "ticker",
               ticker, start_ts, end_ts)
    if df.empty:
        return pd.DataFrame(columns=["ts", "atm_iv", "spot", "expiry"])
    return df