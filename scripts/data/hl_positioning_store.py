"""hl_positioning_store.py — HermesForge US-186: liquidation-events store.

The ONLY new persistent store US-186 introduces is liquidation EVENTS (the OI /
positioning half reuses hl_assetctx_store). Hyperliquid has NO public liquidation
feed (flag F-A), so the event source is OKX ``public/liquidation-orders`` — a
CROSS-VENUE (OKX) feed with a SHALLOW rolling window. It measures OKX leverage
flush, not HL; that is the honest limit this store makes explicit.

Schema (per architect_us186_188_spec.md §1.4): a ``liq_events`` table deduped on
a HEURISTIC composite key ``(inst_id, ts, pos_side, side, sz)`` (flag F-C — OKX
details rows carry no unique order id, so a same-ms same-size same-side duplicate
has a non-zero but astronomically-small residual risk). ``INSERT OR IGNORE`` gives
idempotent, atomic append exactly like the other stores. ``sz`` is stored in OKX
CONTRACTS; ``sz_usd`` = sz * ctVal * bk_px is derived at ingest (ctVal comes from
the OKX instruments endpoint, never hardcoded); failure to resolve ctVal => NULL.

Store location: ~/.hermes/market_data/hl_positioning/liquidations.db

Import direction is one-way and acyclic:
  ingest_okx_liq.py -> hl_positioning_store.py + okx_proxy.HL_TO_OKX
"""

from __future__ import annotations

import sqlite3
import pathlib

import pandas as pd

STORE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_positioning"
DB_NAME = "liquidations.db"

PRAGMAS = (
    "PRAGMA journal_mode=WAL;",
    "PRAGMA synchronous=NORMAL;",
    "PRAGMA foreign_keys=ON;",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS liq_events (
    inst_id   TEXT    NOT NULL,   -- OKX instId e.g. 'BTC-USDT-SWAP'
    ts        INTEGER NOT NULL,   -- details.ts, ms epoch
    pos_side  TEXT    NOT NULL,   -- 'long' | 'short'   (liquidated side)
    side      TEXT    NOT NULL,   -- 'buy' | 'sell'      (closing order side)
    sz        REAL    NOT NULL,   -- contracts
    sz_usd    REAL,               -- sz * ctVal * bk_px (derived at ingest)
    bk_px     REAL,               -- bankruptcy price
    PRIMARY KEY (inst_id, ts, pos_side, side, sz)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS idx_liq_inst_ts ON liq_events (inst_id, ts);

CREATE TABLE IF NOT EXISTS ingest_state (
    inst_id  TEXT PRIMARY KEY,
    last_poll_ts INTEGER NOT NULL,   -- highest event ts written for this inst
    last_run TEXT NOT NULL           -- ISO-8601 UTC
);
"""


def db_path() -> pathlib.Path:
    """STORE_DIR / DB_NAME."""
    return STORE_DIR / DB_NAME


def open_store() -> sqlite3.Connection:
    """Open (create if absent) the liquidations DB; apply PRAGMAs; run schema
    DDL idempotently. Returns a connection in WAL mode."""
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    for pragma in PRAGMAS:
        conn.execute(pragma)
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def append_liqs(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """INSERT OR IGNORE keyed (inst_id, ts, pos_side, side, sz). rows =
    [{inst_id, ts, pos_side, side, sz, sz_usd, bk_px}]. Idempotent (re-polling
    an overlapping window inserts 0). Commit inside; rollback on error. Returns
    count of NEW rows."""
    if not rows:
        return 0
    tuples = [
        (str(r["inst_id"]), int(r["ts"]), str(r["pos_side"]), str(r["side"]),
         float(r["sz"]), r.get("sz_usd"), r.get("bk_px"))
        for r in rows
    ]
    sql = ("INSERT OR IGNORE INTO liq_events "
           "(inst_id, ts, pos_side, side, sz, sz_usd, bk_px) "
           "VALUES (?,?,?,?,?,?,?)")
    try:
        cur = conn.executemany(sql, tuples)
        conn.commit()
        return cur.rowcount if cur.rowcount is not None else 0
    except Exception:
        conn.rollback()
        raise


def upsert_state(conn: sqlite3.Connection, inst_id: str, last_poll_ts: int,
                 last_run: str) -> None:
    """INSERT OR REPLACE ingest_state high-water mark."""
    conn.execute(
        "INSERT OR REPLACE INTO ingest_state (inst_id, last_poll_ts, last_run) "
        "VALUES (?,?,?)",
        (inst_id, int(last_poll_ts), last_run),
    )
    conn.commit()


def last_poll_ts(conn: sqlite3.Connection, inst_id: str) -> int | None:
    """Highest event ts written for inst_id, or None (never ingested)."""
    row = conn.execute(
        "SELECT MAX(ts) FROM liq_events WHERE inst_id=?", (inst_id,)
    ).fetchone()
    return row[0] if row and row[0] is not None else None


def coverage(conn: sqlite3.Connection, inst_id: str) -> dict:
    """{'inst_id','min_ts','max_ts','n'} — earliest/latest stored liquidation."""
    row = conn.execute(
        "SELECT MIN(ts), MAX(ts), COUNT(*) FROM liq_events WHERE inst_id=?",
        (inst_id,),
    ).fetchone()
    return {"inst_id": inst_id, "min_ts": row[0], "max_ts": row[1],
            "n": row[2]}


def read_liqs(inst_id: str, start_ts: int | None = None,
              end_ts: int | None = None) -> pd.DataFrame:
    """DataFrame[inst_id, ts, pos_side, side, sz, sz_usd, bk_px] ascending in
    [start_ts, end_ts)."""
    where = ["inst_id = ?"]
    params: list = [inst_id]
    if start_ts is not None:
        where.append("ts >= ?")
        params.append(int(start_ts))
    if end_ts is not None:
        where.append("ts < ?")
        params.append(int(end_ts))
    sql = ("SELECT inst_id, ts, pos_side, side, sz, sz_usd, bk_px "
           "FROM liq_events WHERE " + " AND ".join(where) + " ORDER BY ts ASC")
    conn = open_store()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()
    if df.empty:
        df = pd.DataFrame(columns=["inst_id", "ts", "pos_side", "side", "sz",
                                   "sz_usd", "bk_px"])
    return df.reset_index(drop=True)