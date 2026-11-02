"""
hl_bar_store.py — HermesForge US-177: Hyperliquid source-of-truth bar store.

A persistent, same-venue store for OHLCV bars fetched from Hyperliquid, so the
bar-level re-simulation / backtest path has ONE authoritative, dedup-safe,
incremental-append data source instead of TTL-overwritten parquet caches.

Design (per architect_us177_spec.md):
  * SQLite per timeframe (stdlib only) — NO pyarrow/fastparquet dependency at
    either ingest or read time. This closes the exact failure class that
    blocked the prior full-window re-simulation (US-168).
  * `INSERT OR IGNORE` on PRIMARY KEY (ticker, timeframe, ts) gives atomic,
    idempotent append for free (re-fetching an overlapping window inserts 0).
  * `bars` table is pure Hyperliquid by construction. The `source` label is
    added only by `load_bars()` (unified reader) when the OKX proxy fills a
    pre-store gap.

Retention policy (US-197): the store is APPEND-ONLY and UNBOUNDED. There is
deliberately NO purge / delete / trim path anywhere in this module or the
ingest pipeline — bars are retained going forward and bounded only by disk.
The ~17-day figure that appears in older notes is Hyperliquid's OWN
candleSnapshot retention floor (the API only serves ~17 days of 5m history),
NOT a store-side purge. The store itself accumulates every bar it has ever
ingested (INSERT OR IGNORE never deletes). See DISK_GROWTH_ESTIMATE_* below.

Store location: ~/.hermes/market_data/hl_bars/  (outside the git repo).

Import direction is one-way and acyclic:
  ingest_hl_bars.py -> hl_bar_store.py + hermes_config.universe
  okx_proxy.py is standalone (no store import)
  hl_bar_store.load_bars() lazily imports okx_proxy.
"""

from __future__ import annotations

import sqlite3
import pathlib
import sys
from enum import Enum

import pandas as pd

# Ensure the sibling okx_proxy module (same directory) is importable whether
# this module is imported as part of a package or flat via sys.path insertion
# (the repo's existing convention, cf. fetch_intraday_crypto.py).
_MODULE_DIR = pathlib.Path(__file__).resolve().parent
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

STORE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_bars"

# Retention / disk-growth baseline (US-197): 5m at 288 bars/ticker/day × 35
# tickers ≈ 10,080 bars/day ≈ 3.68M bars/year; ~100 bytes/row (WITHOUT ROWID +
# index) ≈ 0.4 GB/year. 15m/1h/4h add ≤ 1/3 of that if ever enabled. There is
# NO purge; this is purely an unbounded-growth planning figure for US-201.
DISK_GROWTH_ESTIMATE_BARS_PER_DAY = 10_080
DISK_GROWTH_ESTIMATE_BYTES_PER_YEAR = 400 * 1024 * 1024  # ~0.4 GB

# timeframe -> db filename (normalize the Hyperliquid interval token).
TIMEFRAME_FILES = {
    "5m": "bars_5m.db",
    "15m": "bars_15m.db",
    "1h": "bars_1h.db",
    "4h": "bars_4h.db",
    "1d": "bars_1d.db",
}

PRAGMAS = (
    "PRAGMA journal_mode=WAL;",
    "PRAGMA synchronous=NORMAL;",
    "PRAGMA foreign_keys=ON;",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS bars (
    ticker    TEXT    NOT NULL,
    timeframe TEXT    NOT NULL,
    ts        INTEGER NOT NULL,          -- bar OPEN time, ms epoch UTC (= HL 't')
    open      REAL    NOT NULL,
    high      REAL    NOT NULL,
    low       REAL    NOT NULL,
    close     REAL    NOT NULL,
    volume    REAL    NOT NULL,          -- base-asset volume (= HL 'v')
    trades    INTEGER,                   -- (= HL 'n'); nullable, kept for realism
    PRIMARY KEY (ticker, timeframe, ts)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS idx_bars_ts ON bars (timeframe, ts);

CREATE TABLE IF NOT EXISTS ingest_state (
    ticker    TEXT    NOT NULL,
    timeframe TEXT    NOT NULL,
    last_ts   INTEGER NOT NULL,          -- highest bar open-time written
    last_run  TEXT    NOT NULL,          -- ISO-8601 UTC of last successful run
    PRIMARY KEY (ticker, timeframe)
);
"""


class BarSource(str, Enum):
    HYPERLIQUID = "hyperliquid"
    OKX_PROXY = "okx_proxy"  # pre-store gap ONLY — always labeled


def db_path(timeframe: str) -> pathlib.Path:
    """STORE_DIR / TIMEFRAME_FILES[timeframe] (KeyError on unknown interval)."""
    return STORE_DIR / TIMEFRAME_FILES[timeframe]


def open_store(timeframe: str) -> sqlite3.Connection:
    """Open (create if absent) the timeframe DB; apply PRAGMAs; run schema DDL
    + secondary index idempotently. Returns a connection in WAL mode."""
    path = db_path(timeframe)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    for pragma in PRAGMAS:
        conn.execute(pragma)
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def append_bars(conn: sqlite3.Connection, ticker: str, timeframe: str,
                bars: list[dict]) -> int:
    """INSERT OR IGNORE each bar keyed on (ticker, timeframe, ts). Dedup-safe:
    re-fetching an overlapping window inserts 0 for existing keys. Returns the
    count of NEW rows. Commits inside; rolls back on error (atomic — never
    partial)."""
    if not bars:
        return 0
    # Ticker is matched EXACTLY as canonical (Hyperliquid coin names are
    # case-sensitive: kBONK != KBONK). The universe holds the canonical case.
    rows = []
    for b in bars:
        rows.append((
            ticker, timeframe, int(b["ts"]),
            float(b["open"]), float(b["high"]), float(b["low"]), float(b["close"]),
            float(b["volume"]),
            int(b["trades"]) if b.get("trades") is not None else None,
        ))
    sql = ("INSERT OR IGNORE INTO bars "
           "(ticker, timeframe, ts, open, high, low, close, volume, trades) "
           "VALUES (?,?,?,?,?,?,?,?,?)")
    try:
        cur = conn.executemany(sql, rows)
        conn.commit()
        return cur.rowcount if cur.rowcount is not None else 0
    except Exception:
        conn.rollback()
        raise


def upsert_state(conn: sqlite3.Connection, ticker: str, timeframe: str,
                 last_ts: int, last_run: str) -> None:
    """INSERT OR REPLACE ingest_state high-water mark."""
    conn.execute(
        "INSERT OR REPLACE INTO ingest_state (ticker, timeframe, last_ts, last_run) "
        "VALUES (?,?,?,?)",
        (ticker, timeframe, int(last_ts), last_run),
    )
    conn.commit()


def last_ts(conn: sqlite3.Connection, ticker: str, timeframe: str) -> int | None:
    """Highest stored bar open-time for (ticker, timeframe), or None (never
    ingested)."""
    row = conn.execute(
        "SELECT MAX(ts) FROM bars WHERE ticker=? AND timeframe=?",
        (ticker, timeframe),
    ).fetchone()
    return row[0] if row and row[0] is not None else None


def coverage(conn: sqlite3.Connection, ticker: str, timeframe: str) -> dict:
    """{'ticker','timeframe','min_ts','max_ts','n_bars'} — earliest/latest
    stored bar. min_ts is the store's authoritative floor; ANY read below
    min_ts is a pre-store gap."""
    row = conn.execute(
        "SELECT MIN(ts), MAX(ts), COUNT(*) FROM bars WHERE ticker=? AND timeframe=?",
        (ticker, timeframe),
    ).fetchone()
    return {
        "ticker": ticker,
        "timeframe": timeframe,
        "min_ts": row[0],
        "max_ts": row[1],
        "n_bars": row[2],
    }


def _read_bars(conn: sqlite3.Connection, ticker: str, timeframe: str,
               start_ts: int | None = None, end_ts: int | None = None) -> pd.DataFrame:
    """Read store rows for (ticker, timeframe) in [start_ts, end_ts) ascending."""
    where = ["ticker = ?", "timeframe = ?"]
    params: list = [ticker, timeframe]
    if start_ts is not None:
        where.append("ts >= ?")
        params.append(int(start_ts))
    if end_ts is not None:
        where.append("ts < ?")
        params.append(int(end_ts))
    sql = ("SELECT ts, open, high, low, close, volume, trades FROM bars "
           "WHERE " + " AND ".join(where) + " ORDER BY ts ASC")
    df = pd.read_sql_query(sql, conn, params=params)
    if df.empty:
        df = pd.DataFrame(columns=["ts", "open", "high", "low", "close",
                                   "volume", "trades"])
    return df.reset_index(drop=True)


def read_bars(ticker: str, timeframe: str, start_ts: int | None = None,
              end_ts: int | None = None) -> pd.DataFrame:
    """Read store rows for (ticker, timeframe) in [start_ts, end_ts) ascending.
    No source column (store is pure Hyperliquid by construction). Returns
    DataFrame[ts, open, high, low, close, volume, trades]."""
    conn = open_store(timeframe)
    try:
        return _read_bars(conn, ticker, timeframe, start_ts, end_ts)
    finally:
        conn.close()


def load_bars(ticker: str, timeframe: str, start_ts: int, end_ts: int,
              allow_proxy: bool = True) -> pd.DataFrame:
    """Union-of-sources read for a backtest/paper window.

    1. Read store rows in [start_ts, end_ts)          -> source='hyperliquid'.
    2. If allow_proxy and the store misses the LOW end (start_ts <
       coverage.min_ts, or the ticker has never been ingested): fetch OKX proxy
       bars for [start_ts, min_ts)                    -> source='okx_proxy'.
    3. Concatenate, dedup on ts (store wins on collision), sort ascending.
    4. Every returned row carries a labeled 'source' column, so the proxy
       caveat rides the data and is never implicit.

    Never fabricates, never silently mixes venues across an overlapping range.
    """
    start_ts = int(start_ts)
    end_ts = int(end_ts)

    conn = open_store(timeframe)
    try:
        cov = coverage(conn, ticker, timeframe)
        store = _read_bars(conn, ticker, timeframe, start_ts, end_ts).copy()
    finally:
        conn.close()

    store["source"] = BarSource.HYPERLIQUID.value
    frames = [store]

    if allow_proxy:
        min_ts = cov.get("min_ts")
        # The proxy only ever fills the LOW end: [start_ts, min_ts). If the
        # ticker has never been ingested (min_ts is None), the whole window is
        # a pre-store gap and the proxy is asked for all of it.
        gap_end = end_ts if min_ts is None else min(min_ts, end_ts)
        if gap_end > start_ts:
            try:
                import okx_proxy  # lazily import the standalone proxy
                proxy = okx_proxy.fetch_okx_bars(ticker, timeframe, start_ts, gap_end)
            except Exception:
                proxy = pd.DataFrame()
            if proxy is not None and not proxy.empty:
                proxy = proxy.copy()
                # Align to the canonical bar schema (trades is nullable).
                if "trades" not in proxy.columns:
                    proxy["trades"] = None
                proxy = proxy[["ts", "open", "high", "low", "close", "volume", "trades"]]
                proxy["source"] = BarSource.OKX_PROXY.value
                frames.append(proxy)

    if len(frames) == 1 and frames[0].empty:
        # Return an empty frame with the canonical columns + source label.
        out = pd.DataFrame(columns=["ts", "open", "high", "low", "close",
                                    "volume", "trades", "source"])
        return out

    out = pd.concat(frames, ignore_index=True)
    # Dedup on ts in concat order (store listed first -> store wins), then sort.
    out = out.drop_duplicates(subset="ts", keep="first")
    out = out.sort_values("ts").reset_index(drop=True)
    return out[["ts", "open", "high", "low", "close", "volume", "trades", "source"]]