"""hl_assetctx_store.py — HermesForge US-185: Hyperliquid assetCtxs snapshot store.

Persistent, same-venue store for the REAL mark/oracle/funding/premium/OI
snapshot field ``assetCtxs`` from Hyperliquid's ``metaAndAssetCtxs`` info
endpoint. This is the ONLY honest historical source for the perp mark-vs-oracle
basis, because HL exposes NO ``markPx``/``oraclePx`` history endpoint — the real
basis can only be accumulated GOING FORWARD by snapshotting ``metaAndAssetCtxs``
periodically (F3, accepted).

Design (per architect_us185_spec.md §2.3, mirroring hl_funding_store US-179):
  * SQLite, stdlib-only for write (sqlite3 + pathlib); pandas for read.
  * ``INSERT OR IGNORE`` on PRIMARY KEY (coin, time) gives atomic, idempotent
    append (re-snapshotting the same hour inserts 0).
  * ``read_basis`` returns DataFrame[time, mark_px, oracle_px, basis_bps] where
    basis_bps = (mark_px - oracle_px)/oracle_px * 1e4 (signed, the REAL basis).
  * ``funding``/``premium``/``open_interest`` are kept for provenance only; the
    funding-carry BASIS path reads mark_px/oracle_px, never premium.

Store location: ~/.hermes/market_data/hl_assetctx/  (outside the git repo).

Import direction is one-way and acyclic:
  ingest_hl_assetctx.py -> hl_assetctx_store.py + hermes_config.universe
  funding_carry.py      -> hl_assetctx_store.py (+ hl_funding_store, fee_source,
                           g3_gate)
"""

from __future__ import annotations

import sqlite3
import pathlib

import pandas as pd

STORE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_assetctx"
DB_NAME = "assetctx.db"

# Cadence of snapshotting (hours). Snapshot once/hour returns all coins in ONE
# metaAndAssetCtxs call — no per-coin pagination. [tunable]
SNAPSHOT_INTERVAL_HOURS = 1

PRAGMAS = (
    "PRAGMA journal_mode=WAL;",
    "PRAGMA synchronous=NORMAL;",
    "PRAGMA foreign_keys=ON;",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS asset_ctx (
    coin          TEXT    NOT NULL,
    time          INTEGER NOT NULL,   -- snapshot time, ms epoch
    mark_px       REAL,               -- assetCtxs markPx
    oracle_px     REAL,               -- assetCtxs oraclePx
    funding       REAL,               -- assetCtxs funding (current hourly)
    premium       REAL,               -- assetCtxs premium (impact-price; provenance)
    open_interest REAL,               -- base coin units
    day_ntl_vlm   REAL,               -- assetCtxs.dayNtlVlm  (USD notional, 24h) [US-186]
    day_base_vlm  REAL,               -- assetCtxs.dayBaseVlm (base volume, 24h)  [US-186]
    prev_day_px   REAL,               -- assetCtxs.prevDayPx                        [US-186]
    PRIMARY KEY (coin, time)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS idx_assetctx_coin_time ON asset_ctx (coin, time);
"""


def db_path() -> pathlib.Path:
    """STORE_DIR / DB_NAME."""
    return STORE_DIR / DB_NAME


def open_store() -> sqlite3.Connection:
    """Open (create if absent) the assetctx DB; apply PRAGMAs; run schema DDL
    idempotently, including a non-destructive column migration for the US-186
    extension fields (day_ntl_vlm / day_base_vlm / prev_day_px) so a store
    seeded by the pre-US-186 schema is upgraded in place (existing rows get
    NULL for the new columns, never dropped). Returns a WAL-mode connection."""
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    for pragma in PRAGMAS:
        conn.execute(pragma)
    conn.executescript(_SCHEMA)
    _migrate_columns(conn)
    conn.commit()
    return conn


_NEW_COLUMNS = ("day_ntl_vlm", "day_base_vlm", "prev_day_px")


def _migrate_columns(conn: sqlite3.Connection) -> None:
    """Add missing US-186 columns to an existing asset_ctx table (idempotent;
    no-op for fresh DBs that already carry them in _SCHEMA)."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(asset_ctx)")}
    for col in _NEW_COLUMNS:
        if col not in cols:
            conn.execute(f"ALTER TABLE asset_ctx ADD COLUMN {col} REAL")


def append_snapshot(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """INSERT OR IGNORE keyed (coin, time). rows = [{coin:str, time:int ms,
    mark_px:float|None, oracle_px:float|None, funding:float|None,
    premium:float|None, open_interest:float|None, day_ntl_vlm:float|None,
    day_base_vlm:float|None, prev_day_px:float|None}]. Idempotent:
    re-snapshotting the same (coin,time) inserts 0. Commit inside; rollback on
    error (atomic). Returns count of NEW rows."""
    if not rows:
        return 0
    tuples = [
        (str(r["coin"]), int(r["time"]), _f(r.get("mark_px")),
         _f(r.get("oracle_px")), _f(r.get("funding")),
         _f(r.get("premium")), _f(r.get("open_interest")),
         _f(r.get("day_ntl_vlm")), _f(r.get("day_base_vlm")),
         _f(r.get("prev_day_px")))
        for r in rows
    ]
    sql = ("INSERT OR IGNORE INTO asset_ctx "
           "(coin, time, mark_px, oracle_px, funding, premium, open_interest, "
           "day_ntl_vlm, day_base_vlm, prev_day_px) "
           "VALUES (?,?,?,?,?,?,?,?,?,?)")
    try:
        cur = conn.executemany(sql, tuples)
        conn.commit()
        return cur.rowcount if cur.rowcount is not None else 0
    except Exception:
        conn.rollback()
        raise


def _f(v):
    """Coerce to float-compatible, returning None for None / non-finite."""
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f


def read_basis(coin: str, start_ts: int | None = None,
               end_ts: int | None = None) -> pd.DataFrame:
    """DataFrame[time, mark_px, oracle_px, basis_bps] ascending in
    [start_ts, end_ts). basis_bps = (mark_px - oracle_px)/oracle_px * 1e4
    (signed REAL basis); NaN where oracle_px is missing/<=0."""
    where = ["coin = ?"]
    params: list = [coin]
    if start_ts is not None:
        where.append("time >= ?")
        params.append(int(start_ts))
    if end_ts is not None:
        where.append("time < ?")
        params.append(int(end_ts))
    sql = ("SELECT time, mark_px, oracle_px FROM asset_ctx WHERE "
           + " AND ".join(where) + " ORDER BY time ASC")
    conn = open_store()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()
    if df.empty:
        return pd.DataFrame(columns=["time", "mark_px", "oracle_px", "basis_bps"])
    oracle = df["oracle_px"].astype(float)
    mark = df["mark_px"].astype(float)
    basis = pd.Series(float("nan"), index=df.index)
    mask = oracle > 0
    basis[mask] = (mark[mask] - oracle[mask]) / oracle[mask] * 1e4
    df["basis_bps"] = basis.to_numpy()
    return df[["time", "mark_px", "oracle_px", "basis_bps"]].reset_index(drop=True)


def read_positioning(coin: str, start_ts: int | None = None,
                     end_ts: int | None = None) -> pd.DataFrame:
    """US-186 positioning reader. DataFrame[time, mark_px, open_interest,
    oi_usd, funding, premium, day_ntl_vlm, day_base_vlm, prev_day_px] ascending
    in [start_ts, end_ts). oi_usd = open_interest * mark_px (HL openInterest is
    BASE units). Consecutive rows feed the OI-delta quadrant proxy
    (gauntlet/oi_delta.classify_oi_delta). Long/short OI is NOT available on HL
    (flag F-B) — no long_oi/short_oi columns."""
    where = ["coin = ?"]
    params: list = [coin]
    if start_ts is not None:
        where.append("time >= ?")
        params.append(int(start_ts))
    if end_ts is not None:
        where.append("time < ?")
        params.append(int(end_ts))
    sql = ("SELECT time, mark_px, open_interest, funding, premium, "
           "day_ntl_vlm, day_base_vlm, prev_day_px FROM asset_ctx WHERE "
           + " AND ".join(where) + " ORDER BY time ASC")
    conn = open_store()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()
    if df.empty:
        return pd.DataFrame(columns=["time", "mark_px", "open_interest",
                                     "oi_usd", "funding", "premium",
                                     "day_ntl_vlm", "day_base_vlm",
                                     "prev_day_px"])
    df["oi_usd"] = df["open_interest"].astype(float) * df["mark_px"].astype(float)
    return df.reset_index(drop=True)


def read_assetctx(coin: str, start_ts: int | None = None,
                  end_ts: int | None = None) -> pd.DataFrame:
    """Full-row reader (provenance): DataFrame[time, mark_px, oracle_px,
    funding, premium, open_interest] ascending in [start_ts, end_ts)."""
    where = ["coin = ?"]
    params: list = [coin]
    if start_ts is not None:
        where.append("time >= ?")
        params.append(int(start_ts))
    if end_ts is not None:
        where.append("time < ?")
        params.append(int(end_ts))
    sql = ("SELECT time, mark_px, oracle_px, funding, premium, open_interest "
           "FROM asset_ctx WHERE " + " AND ".join(where) + " ORDER BY time ASC")
    conn = open_store()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()
    if df.empty:
        return pd.DataFrame(columns=["time", "mark_px", "oracle_px", "funding",
                                     "premium", "open_interest"])
    return df.reset_index(drop=True)


def last_snapshot_ts(conn: sqlite3.Connection, coin: str) -> int | None:
    """Highest stored snapshot time for coin, or None (never snapshotted)."""
    row = conn.execute(
        "SELECT MAX(time) FROM asset_ctx WHERE coin=?", (coin,)
    ).fetchone()
    return row[0] if row and row[0] is not None else None


def coverage(conn: sqlite3.Connection, coin: str) -> dict:
    """{'coin','min_ts','max_ts','n'} — earliest/latest stored snapshot."""
    row = conn.execute(
        "SELECT MIN(time), MAX(time), COUNT(*) FROM asset_ctx WHERE coin=?",
        (coin,),
    ).fetchone()
    return {"coin": coin, "min_ts": row[0], "max_ts": row[1], "n": row[2]}