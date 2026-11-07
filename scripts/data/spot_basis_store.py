"""spot_basis_store.py — HermesForge US-229: forward spot-vs-oracle basis store.

The delta-neutral funding carry (long-spot / short-perp) hedges with a REAL
spot leg, but today that hedge is PROXIED by the HL perp oracle — the one
UNMEASURED input the strategy flags (HYP-29: the spot ask/bid spread is an
ASSUMED input, because no L2 spot book is held). This store accumulates the
real spot price (a liquid-CEX last — OKX) against the HL oracle going forward,
so the hedge stops being a proxy over the paper-forward accumulation window
(gauntlet rule: 6-12 months before any promotion).

spot_basis_bps = (spot_px - oracle_px) / oracle_px * 1e4   (signed)

This measures the TRUE spot-vs-oracle divergence — a DIFFERENT quantity from:
  * the mark-vs-oracle basis in hl_assetctx_store.read_basis (the perp MARK vs
    oracle, which is what funding_carry's basis_widen kill-stop reads), and
  * the cross-venue HL-mark-vs-OKX-last price basis in basis_store (a
    mark-vs-spot read, not spot-vs-oracle).

Store location: ~/.hermes/market_data/spot_basis/  (outside the git repo).

Import direction is one-way and acyclic:
  ingest_crossvenue_basis.py -> spot_basis_store.py (+ okx_proxy,
                                hl_assetctx_store)   [the spot leg + oracle leg]
  funding_carry_paper.py     -> spot_basis_store.py  [read-side, paper driver]
"""

from __future__ import annotations

import sqlite3
import pathlib
import time

import pandas as pd

STORE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "spot_basis"
DB_NAME = "spot_basis.db"

# Provenance of the spot leg. Until a real L2 spot book is held, the spot price
# is the OKX last (a real, liquid-CEX tradable price) — NOT silently credited as
# a mid/fill; the paper driver re-validates the spread assumption against it.
SPOT_SOURCE_OKX_LAST = "okx_last"
SOURCES = (SPOT_SOURCE_OKX_LAST,)

PRAGMAS = (
    "PRAGMA journal_mode=WAL;",
    "PRAGMA synchronous=NORMAL;",
    "PRAGMA foreign_keys=ON;",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS spot_basis (
    coin           TEXT    NOT NULL,
    time           INTEGER NOT NULL,   -- snapshot time ms (hour-bucketed)
    spot_px        REAL,               -- real spot price (OKX last)
    oracle_px      REAL,               -- HL perp oracle (assetCtxs oraclePx)
    spot_basis_bps REAL,               -- (spot_px - oracle_px)/oracle_px * 1e4
    source         TEXT    NOT NULL DEFAULT 'okx_last',
    PRIMARY KEY (coin, time)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS idx_spot_basis_coin_time ON spot_basis (coin, time);
"""


def db_path() -> pathlib.Path:
    """STORE_DIR / DB_NAME."""
    return STORE_DIR / DB_NAME


def open_store() -> sqlite3.Connection:
    """Open (create if absent) the spot-basis DB; apply PRAGMAs; schema DDL."""
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    for pragma in PRAGMAS:
        conn.execute(pragma)
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def _f(v):
    """Coerce to float-compatible, returning None for None/non-finite/invalid."""
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f


def compute_spot_basis(spot_px: float | None, oracle_px: float | None) -> float | None:
    """(spot_px - oracle_px)/oracle_px * 1e4 (signed bps); None if undecomposable."""
    if spot_px is None or oracle_px is None or oracle_px <= 0:
        return None
    return (spot_px - oracle_px) / oracle_px * 1e4


def append_spot_basis(conn: sqlite3.Connection, rows: list[dict],
                      source: str = SPOT_SOURCE_OKX_LAST) -> int:
    """INSERT OR IGNORE keyed (coin, time). rows = [{coin:str, time:int ms,
    spot_px:float|None, oracle_px:float|None}]. spot_basis_bps is COMPUTED here
    (never caller-supplied, so a caller cannot silently credit a spread). Commit
    inside; rollback on error. Returns count of NEW rows."""
    if source not in SOURCES:
        source = SPOT_SOURCE_OKX_LAST  # fail-closed: unknown provenance -> okx_last
    tuples = []
    for r in rows:
        spot = _f(r.get("spot_px"))
        oracle = _f(r.get("oracle_px"))
        tuples.append((str(r["coin"]), int(r["time"]), spot, oracle,
                       compute_spot_basis(spot, oracle), source))
    sql = ("INSERT OR IGNORE INTO spot_basis "
           "(coin, time, spot_px, oracle_px, spot_basis_bps, source) "
           "VALUES (?,?,?,?,?,?)")
    try:
        cur = conn.executemany(sql, tuples)
        conn.commit()
        return cur.rowcount if cur.rowcount is not None else 0
    except Exception:
        conn.rollback()
        raise


def _now_ms() -> int:
    return int(time.time() * 1000)


def read_spot_basis(coin: str, start_ts: int | None = None,
                    end_ts: int | None = None) -> pd.DataFrame:
    """DataFrame[time, spot_px, oracle_px, spot_basis_bps, source] ascending in
    [start_ts, end_ts)."""
    where = ["coin = ?"]
    params: list = [coin]
    if start_ts is not None:
        where.append("time >= ?")
        params.append(int(start_ts))
    if end_ts is not None:
        where.append("time < ?")
        params.append(int(end_ts))
    sql = ("SELECT time, spot_px, oracle_px, spot_basis_bps, source "
           "FROM spot_basis WHERE " + " AND ".join(where) + " ORDER BY time ASC")
    conn = open_store()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()
    if df.empty:
        return pd.DataFrame(columns=["time", "spot_px", "oracle_px",
                                     "spot_basis_bps", "source"])
    return df.reset_index(drop=True)


def coverage(conn: sqlite3.Connection, coin: str) -> dict:
    """{'coin','min_ts','max_ts','n'} — earliest/latest stored snapshot."""
    row = conn.execute(
        "SELECT MIN(time), MAX(time), COUNT(*) FROM spot_basis WHERE coin=?",
        (coin,),
    ).fetchone()
    return {"coin": coin, "min_ts": row[0], "max_ts": row[1], "n": row[2]}