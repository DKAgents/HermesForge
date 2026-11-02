"""basis_store.py — HermesForge US-188: cross-venue (HL vs OKX) basis store.

Stores the raw OKX legs AND the computed HL-vs-OKX join that is the deliverable
"real carry metric" for funding_carry (US-185):

  * ``okx_funding``      — OKX realized 8h funding (deep backfill ~90d),
                           funding_rate = realizedRate (settled 8h decimal).
  * ``okx_ticker``       — OKX last/bid/ask price snapshots (price-basis leg).
  * ``cross_venue_basis`` — the hourly join: funding APR spread + price basis.

Standing limitation (flag F-F): Binance/Bybit are 403 — NOT re-attempted. This
feed is HL-vs-OKX only.

Annualization (architect_us186_188_spec.md §3.3, unit = PERCENT):
    hl_funding_apr  = HL hourly rate      * 8760      * 100
    okx_funding_apr = OKX 8h realizedRate * (365*3)   * 100   (= * 1095 * 100)
    funding_spread_apr = hl_funding_apr - okx_funding_apr   (percent)
    price_basis_bps    = (hl_mark - okx_last) / okx_last * 1e4   (signed bps)

Store location: ~/.hermes/market_data/cross_venue_basis/basis.db

Import direction is one-way and acyclic:
  ingest_crossvenue_basis.py -> basis_store.py + okx_proxy.HL_TO_OKX
                                + hl_funding_store + hl_assetctx_store
  funding_carry.py           -> basis_store.py (+ hl_funding_store,
                                hl_assetctx_store)
"""

from __future__ import annotations

import sqlite3
import pathlib

import pandas as pd

STORE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "cross_venue_basis"
DB_NAME = "basis.db"

PRAGMAS = (
    "PRAGMA journal_mode=WAL;",
    "PRAGMA synchronous=NORMAL;",
    "PRAGMA foreign_keys=ON;",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS okx_funding (
    inst_id        TEXT    NOT NULL,   -- 'BTC-USDT-SWAP'
    ts             INTEGER NOT NULL,   -- fundingTime ms (8h boundary)
    funding_rate   REAL    NOT NULL,   -- realizedRate (8h decimal)
    premium        REAL,               -- current premium (funding-rate endpoint; provenance)
    PRIMARY KEY (inst_id, ts)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS okx_ticker (
    inst_id  TEXT    NOT NULL,
    ts       INTEGER NOT NULL,   -- snapshot time ms (hour-bucketed)
    last     REAL, bid REAL, ask REAL,
    PRIMARY KEY (inst_id, ts)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS cross_venue_basis (
    coin               TEXT    NOT NULL,   -- HL canonical coin ('BTC')
    ts                 INTEGER NOT NULL,   -- snapshot time ms (hourly)
    hl_funding_apr     REAL,               -- annualized HL hourly rate (percent)
    okx_funding_apr    REAL,               -- annualized OKX 8h rate (percent)
    funding_spread_apr REAL,               -- hl - okx (percent)
    hl_mark            REAL,
    okx_last           REAL,
    price_basis_bps    REAL,               -- (hl_mark - okx_last)/okx_last * 1e4
    PRIMARY KEY (coin, ts)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_cvb_coin_ts ON cross_venue_basis (coin, ts);

CREATE TABLE IF NOT EXISTS ingest_state (
    feed     TEXT    NOT NULL,   -- 'okx_funding' | 'okx_ticker' | 'basis'
    key      TEXT    NOT NULL,   -- inst_id or coin
    last_ts  INTEGER NOT NULL,
    last_run TEXT    NOT NULL,
    PRIMARY KEY (feed, key)
) WITHOUT ROWID;
"""


def db_path() -> pathlib.Path:
    """STORE_DIR / DB_NAME."""
    return STORE_DIR / DB_NAME


def open_store() -> sqlite3.Connection:
    """Open (create if absent) the basis DB; apply PRAGMAs; run schema DDL
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
    if not tuples:
        return 0
    try:
        cur = conn.executemany(sql, tuples)
        conn.commit()
        return cur.rowcount if cur.rowcount is not None else 0
    except Exception:
        conn.rollback()
        raise


def _f(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def append_okx_funding(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """rows = [{inst_id, ts, funding_rate, premium}]. Keyed (inst_id, ts)."""
    tuples = [(str(r["inst_id"]), int(r["ts"]), float(r["funding_rate"]),
               _f(r.get("premium"))) for r in rows]
    return _append(conn, "INSERT OR IGNORE INTO okx_funding "
                   "(inst_id, ts, funding_rate, premium) VALUES (?,?,?,?)",
                   tuples)


def append_okx_ticker(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """rows = [{inst_id, ts, last, bid, ask}]. Keyed (inst_id, ts)."""
    tuples = [(str(r["inst_id"]), int(r["ts"]), _f(r.get("last")),
               _f(r.get("bid")), _f(r.get("ask"))) for r in rows]
    return _append(conn, "INSERT OR IGNORE INTO okx_ticker "
                   "(inst_id, ts, last, bid, ask) VALUES (?,?,?,?,?)", tuples)


def append_basis(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """rows = [{coin, ts, hl_funding_apr, okx_funding_apr, funding_spread_apr,
    hl_mark, okx_last, price_basis_bps}]. Keyed (coin, ts)."""
    tuples = [(str(r["coin"]), int(r["ts"]), _f(r.get("hl_funding_apr")),
               _f(r.get("okx_funding_apr")), _f(r.get("funding_spread_apr")),
               _f(r.get("hl_mark")), _f(r.get("okx_last")),
               _f(r.get("price_basis_bps"))) for r in rows]
    return _append(conn, "INSERT OR IGNORE INTO cross_venue_basis "
                   "(coin, ts, hl_funding_apr, okx_funding_apr, "
                   "funding_spread_apr, hl_mark, okx_last, price_basis_bps) "
                   "VALUES (?,?,?,?,?,?,?,?)", tuples)


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


def read_okx_funding(inst_id: str, start_ts: int | None = None,
                     end_ts: int | None = None) -> pd.DataFrame:
    """DataFrame[ts, funding_rate, premium] ascending."""
    df = _read("ts, funding_rate, premium", "okx_funding", "inst_id", inst_id,
               start_ts, end_ts)
    if df.empty:
        return pd.DataFrame(columns=["ts", "funding_rate", "premium"])
    return df


def read_ticker(inst_id: str, start_ts: int | None = None,
                end_ts: int | None = None) -> pd.DataFrame:
    """DataFrame[ts, last, bid, ask] ascending."""
    df = _read("ts, last, bid, ask", "okx_ticker", "inst_id", inst_id,
               start_ts, end_ts)
    if df.empty:
        return pd.DataFrame(columns=["ts", "last", "bid", "ask"])
    return df


def read_basis(coin: str, start_ts: int | None = None,
               end_ts: int | None = None) -> pd.DataFrame:
    """DataFrame[ts, hl_funding_apr, okx_funding_apr, funding_spread_apr,
    hl_mark, okx_last, price_basis_bps] ascending."""
    df = _read("ts, hl_funding_apr, okx_funding_apr, funding_spread_apr, "
               "hl_mark, okx_last, price_basis_bps", "cross_venue_basis",
               "coin", coin, start_ts, end_ts)
    if df.empty:
        return pd.DataFrame(columns=["ts", "hl_funding_apr", "okx_funding_apr",
                                     "funding_spread_apr", "hl_mark",
                                     "okx_last", "price_basis_bps"])
    return df