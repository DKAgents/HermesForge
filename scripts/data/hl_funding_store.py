"""hl_funding_store.py — HermesForge US-179: Hyperliquid funding-rate store.

A persistent, same-venue store for hourly funding-rate + premium history fetched
from Hyperliquid's ``fundingHistory`` info endpoint, so the funding/basis-carry
backtest path (funding_carry.py) has ONE authoritative, dedup-safe,
incremental-append data source instead of the TTL-overwritten parquet cache
(fetch_hyperliquid_metrics.py) which only retains a rolling window.

Design (per architect_us179_180_spec.md §1.1.2, mirroring hl_bar_store US-177):
  * SQLite, stdlib-only for write (sqlite3 + pathlib); pandas for read.
  * ``INSERT OR IGNORE`` on PRIMARY KEY (coin, time) gives atomic, idempotent
    append for free (re-fetching an overlapping window inserts 0).
  * Single DB, single table (funding is one time-series, not timeframe-partitioned).
  * ``ingest_state`` holds the high-water mark (highest settlement time written);
    state is only mutated AFTER a fully-successful append.

Store location: ~/.hermes/market_data/hl_funding/  (outside the git repo).

Import direction is one-way and acyclic:
  ingest_hl_funding.py -> hl_funding_store.py + hermes_config.universe
  funding_carry.py     -> hl_funding_store.py (+ fee_source, g3_gate)
"""

from __future__ import annotations

import sqlite3
import pathlib
import sys

import pandas as pd

STORE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_funding"
DB_NAME = "funding.db"

PRAGMAS = (
    "PRAGMA journal_mode=WAL;",
    "PRAGMA synchronous=NORMAL;",
    "PRAGMA foreign_keys=ON;",
)

FUNDING_PAGE = 500  # Hyperliquid cap per fundingHistory call

_SCHEMA = """
CREATE TABLE IF NOT EXISTS funding (
    coin         TEXT    NOT NULL,
    time         INTEGER NOT NULL,   -- settlement time, ms epoch (= HL 'time')
    funding_rate REAL    NOT NULL,   -- HOURLY rate, decimal fraction (e.g. 0.0000125)
    premium      REAL    NOT NULL,   -- HOURLY premium, signed decimal (basis proxy)
    PRIMARY KEY (coin, time)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS idx_funding_coin_time ON funding (coin, time);

CREATE TABLE IF NOT EXISTS ingest_state (
    coin    TEXT PRIMARY KEY,
    last_ts INTEGER NOT NULL,        -- highest funding settlement time written
    last_run TEXT NOT NULL           -- ISO-8601 UTC
);
"""


def db_path() -> pathlib.Path:
    """STORE_DIR / DB_NAME."""
    return STORE_DIR / DB_NAME


def open_store() -> sqlite3.Connection:
    """Open (create if absent) the funding DB; apply PRAGMAs; run schema DDL
    idempotently. Returns a connection in WAL mode."""
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    for pragma in PRAGMAS:
        conn.execute(pragma)
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def append_funding(conn: sqlite3.Connection, coin: str,
                   rows: list[dict]) -> int:
    """INSERT OR IGNORE keyed (coin, time). rows = [{time:int ms,
    funding_rate:float, premium:float}]. Idempotent (re-fetch overlap inserts 0).
    Commit inside; rollback on error (atomic — never partial). Returns count of
    NEW rows."""
    if not rows:
        return 0
    # Coin matched EXACTLY as canonical (HL coin names case-sensitive).
    tuples = [
        (coin, int(r["time"]), float(r["funding_rate"]), float(r["premium"]))
        for r in rows
    ]
    sql = ("INSERT OR IGNORE INTO funding (coin, time, funding_rate, premium) "
           "VALUES (?,?,?,?)")
    try:
        cur = conn.executemany(sql, tuples)
        conn.commit()
        return cur.rowcount if cur.rowcount is not None else 0
    except Exception:
        conn.rollback()
        raise


def upsert_state(conn: sqlite3.Connection, coin: str, last_ts: int,
                 last_run: str) -> None:
    """INSERT OR REPLACE ingest_state high-water mark."""
    conn.execute(
        "INSERT OR REPLACE INTO ingest_state (coin, last_ts, last_run) "
        "VALUES (?,?,?)",
        (coin, int(last_ts), last_run),
    )
    conn.commit()


def last_ts(conn: sqlite3.Connection, coin: str) -> int | None:
    """Highest stored funding settlement time for coin, or None (never ingested)."""
    row = conn.execute(
        "SELECT MAX(time) FROM funding WHERE coin=?", (coin,)
    ).fetchone()
    return row[0] if row and row[0] is not None else None


def coverage(conn: sqlite3.Connection, coin: str) -> dict:
    """{'coin','min_ts','max_ts','n'} — earliest/latest stored settlement."""
    row = conn.execute(
        "SELECT MIN(time), MAX(time), COUNT(*) FROM funding WHERE coin=?",
        (coin,),
    ).fetchone()
    return {"coin": coin, "min_ts": row[0], "max_ts": row[1], "n": row[2]}


def read_funding(coin: str, start_ts: int | None = None,
                 end_ts: int | None = None) -> pd.DataFrame:
    """DataFrame[time, funding_rate, premium] ascending in [start_ts, end_ts)."""
    where = ["coin = ?"]
    params: list = [coin]
    if start_ts is not None:
        where.append("time >= ?")
        params.append(int(start_ts))
    if end_ts is not None:
        where.append("time < ?")
        params.append(int(end_ts))
    sql = ("SELECT time, funding_rate, premium FROM funding WHERE "
           + " AND ".join(where) + " ORDER BY time ASC")
    conn = open_store()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()
    if df.empty:
        df = pd.DataFrame(columns=["time", "funding_rate", "premium"])
    return df.reset_index(drop=True)