# Architect Spec — US-177: Hyperliquid as Single Source of Truth for Crypto Bars

Date: 2026-11-01
Author: Architect (HermesForge)
Status: DESIGN ONLY — no pipeline code, no posts, no cron touched. Awaiting sign-off.
Scope: One coherent design — persistent same-venue Hyperliquid bar store + daily
ingestion + a read path that consumes the store and falls back to the OKX proxy
ONLY for the pre-store history gap (explicitly labeled, shrinking to zero).

## 0. Ground truth read (verified — do not re-derive)

Files read in full:
- scripts/paper_trading/fetch_crypto_data.py    (daily 1d ingest, HL, 980+ bars/coin)
- scripts/paper_trading/fetch_6h_data.py        (6h via 2h→6h resample, HL)
- scripts/data/intraday_provider.py             (unified provider; crypto→hyperliquid,
                                                 5m TTL cache OVERWRITES each fetch)
- scripts/data/fetch_intraday_crypto.py         (candleSnapshot pagination, 500/call)
- scripts/paper_trading/capture_sweep_signals.py (data_source:"hyperliquid" line + intraday)
- scripts/hermes_config/universe.py             (CRYPTO_UNIVERSE, single source of truth)
- scripts/system_doctor/resolve_python.sh        (Rule 1d interpreter resolution)
- scripts/paper_trading/capture_signals_wrapper.sh / capture_sweep_wrapper.sh (cron shape)
- scripts/paper_trading/cron_jobs_backup.json    (cron job schema: no_agent, script, kind:cron)
- 02-Backlog/Stories/US-168 + US-177 (context)

CONFIRMED FACTS:
1. Universe — single source of truth is `scripts/hermes_config/universe.py`
   `CRYPTO_UNIVERSE` (35 tickers incl. BTC/ETH/SOL/.../kBONK/kPEPE/kSHIB).
   All scripts must import it (never re-list). Note: existing fetchers import it
   via `sys.path.insert(0, parent.parent)` then `from hermes_config.universe import
   CRYPTO_UNIVERSE` (fetch_crypto_data.py:31-34).

2. Hyperliquid candle endpoint — POST https://api.hyperliquid.xyz/info with body
   `{"type":"candleSnapshot","req":{"coin":X,"interval":"5m","startTime":ms,"endTime":ms}}`.
   Returns list of `{t,o,h,l,c,v,n}` (t = open time ms epoch). ~500 bars per call.
   Native intervals: 1m/5m/15m/30m/1h/2h/4h/1d (NO 6h — fetched as 2h and resampled).
   ~17 days retention for 5m. 1d is retained deep (980+ bars → 2020).

3. Existing intraday caches are TTL OVERWRITE (NOT append): intraday_provider writes
   `~/.hermes/market_data/{TICKER}_{interval}_hyperliquid.parquet` freshly each 5m;
   fetch_intraday_crypto writes `~/.hermes/market_data/intraday/crypto/{T}_{i}.parquet`.
   Neither can accumulate a window — this is the exact gap US-177 closes.

4. OKX proxy today: `liquidity_heatmap.py` has `fetch_okx_orderbook()` / `fetch_okx_oi()`
   (L2 orderbook + open interest ONLY). There is NO OKX candle-history fetcher in the
   repo — the US-168 full-window re-sim consumed OKX 5m bars as a one-off external
   proxy (documented "46-day OKX proxy" caveat). This design ADDS the canonical
   labeled OKX bar fallback reader (§3.2) so the proxy path is explicit, not ad hoc.

5. Interpreter (Rule 1d): cron `.sh` wrappers MUST resolve the interpreter via
   `PYTHONBIN="$(/root/HermesForge/scripts/system_doctor/resolve_python.sh)"`, never
   bare `python3` (US-163 — bare python3 resolves to dependency-less tools interpreter).

6. DEPENDENCY HARD CONSTRAINT (from US-168): the resolved venv was MISSING
   pyarrow/fastparquet, which is what blocked the prior full-bar re-simulation.
   Therefore the store format MUST NOT require a non-stdlib engine at either ingest
   or read time. This is a deciding factor for §1 (SQLite).

---

## 1. Persistent bar store

### 1.1 Format: SQLite (recommended) — rationale

Choose SQLite per timeframe. NOT parquet, NOT jsonl.

- Zero third-party deps. `sqlite3` is stdlib. The resolved venv already hit a
  pyarrow/fastparquet gap (US-168). SQLite removes that failure class from BOTH the
  daily ingestion AND the backtest read path — both are pure stdlib + requests.
- Atomic + idempotent append via `INSERT OR IGNORE` on a PRIMARY KEY. This is the
  user's HARD rule (atomic writes, no silent partial state) satisfied by the engine,
  not by discipline.
- Append is cheap (append to B-tree in WAL mode); parquet append means rewrite/row-group
  management; jsonl has no dedup or index (full-scan reads only, no cross-sectional query).
- Range queries ("ticker X timeframe Y from ts A→B") are index-seek O(log n).

Trade-off acknowledged: parquet is better for bulk columnar scans of LARGE read sets.
Mitigation: the read path (§3.1) can materialize a parquet snapshot on demand for an
existing backtest if columnar speed is ever needed — but that optional export does NOT
retire the store layer, and it is explicitly out of scope here.

### 1.2 Location

Store root: `~/.hermes/market_data/hl_bars/` (outside the git repo, matching the
existing `~/.hermes/market_data/` convention). MUST be durable across `hermes update`
re-staging — flag to coder: keep this dir out of any staging/wipe path (same protection
status as other market_data parquet caches today).

### 1.3 Schema

Partition by timeframe: one DB file per timeframe. This bounds per-file size, isolates
the high-volume 5m file, and makes per-resolution retention/compute independent.

```
~/.hermes/market_data/hl_bars/
    bars_5m.db
    bars_15m.db        (added later if needed)
    bars_1h.db         (added later if needed)
    ...
```

Per DB, two tables:

```sql
-- bars: one row per canonical (ticker, timeframe, ts); timeframe stored for
-- self-describing dumps even though the filename already implies it.
CREATE TABLE IF NOT EXISTS bars (
    ticker    TEXT    NOT NULL,
    timeframe TEXT    NOT NULL,
    ts        INTEGER NOT NULL,          -- bar OPEN time, ms epoch UTC (= Hyperliquid 't')
    open      REAL    NOT NULL,
    high      REAL    NOT NULL,
    low       REAL    NOT NULL,
    close     REAL    NOT NULL,
    volume    REAL    NOT NULL,          -- base-asset volume (= HL 'v')
    trades    INTEGER,                   -- (= HL 'n'); nullable, keep for realism
    PRIMARY KEY (ticker, timeframe, ts)
) WITHOUT ROWID;

-- ingest_state: high-water mark + provenance per (ticker, timeframe).
CREATE TABLE IF NOT EXISTS ingest_state (
    ticker    TEXT    NOT NULL,
    timeframe TEXT    NOT NULL,
    last_ts   INTEGER NOT NULL,          -- highest bar open-time written
    last_run  TEXT    NOT NULL,          -- ISO-8601 UTC of last successful run
    PRIMARY KEY (ticker, timeframe)
);
```

Indexes: the `WITHOUT ROWID` PRIMARY KEY is a clustered covering index on
(ticker, timeframe, ts), serving point/range reads per ticker. Add one secondary
index for universe-wide time slices:

```sql
CREATE INDEX IF NOT EXISTS idx_bars_ts ON bars (timeframe, ts);
```

Scale/partitioning note: WITHOUT ROWID composite PK keeps row storage compact; the
compound PK removes any need for year-partitioning at projected volume (§4). If a
timeframe ever exceeds ~50M rows, split that timeframe into `bars_5m_YYYY` tables with
a range dispatcher — explicitly deferred, not needed now.

### 1.4 Module + signatures (storage layer)

New module `scripts/data/hl_bar_store.py` (stdlib only: sqlite3, pathlib, pandas
for the read DataFrame). All ingestion and read code goes here; no other file opens
the DB directly.

```python
# scripts/data/hl_bar_store.py

STORE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_bars"
# timeframe -> db filename (normalize the Hyperliquid interval token)
TIMEFRAME_FILES = {"5m": "bars_5m.db", "15m": "bars_15m.db",
                   "1h": "bars_1h.db", "4h": "bars_4h.db", "1d": "bars_1d.db"}
PRAGMAS = ("PRAGMA journal_mode=WAL;", "PRAGMA synchronous=NORMAL;",
           "PRAGMA foreign_keys=ON;")

def db_path(timeframe: str) -> pathlib.Path
    """STORE_DIR / TIMEFRAME_FILES[timeframe] (KeyError on unknown interval)."""

def open_store(timeframe: str) -> sqlite3.Connection
    """Open (create if absent) the timeframe DB; apply PRAGMAs; run schema DDL
    + secondary index idempotently. Returns a connection in WAL mode."""

def append_bars(conn: sqlite3.Connection, ticker: str, timeframe: str,
                bars: list[dict]) -> int
    """INSERT OR IGNORE each bar {ts,open,high,low,close,volume,trades} keyed on
    (ticker,timeframe,ts). Dedup-safe: re-fetching an overlapping window inserts 0
    for existing keys. Returns count of NEW rows. Commit inside; rollback on error
    (atomic — never partial)."""

def upsert_state(conn, ticker: str, timeframe: str, last_ts: int, last_run: str) -> None
    """INSERT OR REPLACE ingest_state high-water mark."""

def last_ts(conn, ticker: str, timeframe: str) -> int | None
    """Highest stored bar open-time for (ticker, timeframe), or None (never ingested)."""

def coverage(conn, ticker: str, timeframe: str) -> dict
    """{'ticker','timeframe','min_ts','max_ts','n_bars'} — earliest/latest stored bar.
    min_ts is the store's authoritative floor; ANY read below min_ts is a pre-store gap."""

def read_bars(ticker: str, timeframe: str, start_ts: int | None = None,
              end_ts: int | None = None) -> pd.DataFrame
    """Read store rows for (ticker,timeframe) in [start_ts, end_ts) ascending,
    no source column (store is pure Hyperliquid by construction). Returns
    DataFrame[ts,open,high,low,close,volume,trades]."""
```

---

## 2. Daily ingestion job

### 2.1 Universe + resolution

- Universe: `from hermes_config.universe import CRYPTO_UNIVERSE` (single source of truth).
  Ingest ALL 35 tickers (cheap: ~35 requests × 1-2 pages per day at 5m).
- Trading resolution: 5m is the STR-Q intraday resolution and THE retention-cliff
  interval (17d). This is the mandatory timeframe. Config list `INGEST_TIMEFRAMES`
  defaults to `["5m"]`; `"15m"/"1h"/"4h"` are add-ons gated behind the same list
  (NOT hardcoded). `1d` is intentionally EXCLUDED from this job — daily bars are
  already retained deep by Hyperliquid and already ingested by fetch_crypto_data.py.

### 2.2 Ingest logic (incremental, idempotent)

```python
HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"
IF = __import__ ...
INGEST_TIMEFRAMES = ["5m"]                 # trading resolution; extendable
MAX_BARS_PER_CALL = 500                    # HL cap, paginate
FIRST_RUN_LOOKBACK_DAYS = 18               # seed slightly beyond the ~17d retention
INCREMENTAL_OVERLAP_MS = 2 * 5 * 60 * 1000 # 2 bars overlap to catch late/finalized tail

def fetch_candles(ticker: str, interval: str, start_ms: int, end_ms: int) -> list[dict]
    """POST candleSnapshot; raise on HTTP!=200; return [] on empty. Parse to
    {ts,open,high,low,close,volume,trades}."""

def incremental_window(conn, ticker: str, timeframe: str) -> tuple[int, int]
    """(start_ms, end_ms) for this run.
    - first run (last_ts() is None): start = now - FIRST_RUN_LOOKBACK_DAYS (seed
      the full retained window; HL bounds the actual reach).
    - subsequent: start = last_ts - INCREMENTAL_OVERLAP_MS (catch tail), end = now."""

def ingest_ticker(conn, ticker: str, timeframe: str) -> dict
    """Paginate fetch_candles from incremental_window()->start to now, append_bars(),
    upsert_state(). Returns {'ticker','timeframe','new_bars','last_ts','window'}.
    Never mutates state on a fetch failure (append only after a full successful page)."""

def ingest_timeframe(timeframe: str, universe: list, dry_run: bool = False) -> dict
    """Loop ingest_ticker over universe; aggregate {'ok','errors','new_bars', ...}.
    Polite 0.2s sleep between tickers (existing convention)."""

def main() -> int
    """argparse --dry-run --timeframes; exit 0 on success, non-zero on hard failure.
    Prints a compact per-ticker summary (not a full dump — matches principal's
    verbosity preference)."""
```

Module `scripts/data/ingest_hl_bars.py`.

### 2.3 Cron shape + interpreter

Wrapper `scripts/data/ingest_hl_bars_wrapper.sh` (mirrors capture_signals_wrapper.sh):

```bash
#!/bin/bash
set -euo pipefail
cd /root/HermesForge
PYTHONBIN="$(/root/HermesForge/scripts/system_doctor/resolve_python.sh)"   # Rule 1d
source /root/.hermes/.env 2>/dev/null
export $(grep -E '^[A-Z_]+=' /root/.hermes/.env | sed 's/=.*//') 2>/dev/null || true
"$PYTHONBIN" scripts/data/ingest_hl_bars.py "$@"
```

Cron entry (no_agent, script wrapper — matching the existing pattern):

```
name:      "Hyperliquid Bar Store Ingest [T3]"
script:    "ingest_hl_bars_wrapper.sh"
no_agent:  true
schedule:  { "kind": "cron", "expr": "10 13 * * *" }   # 13:10 UTC daily
deliver:   "local"
enabled_toolsets: ["terminal"]
```

Rationale: once-daily is sufficient to build the window — 17-day retrieval is ample
headroom against a single missed day, and the store's consumer is the BACKTEST path
(run on demand), not live capture (live capture still reads intraday_provider directly).
13:10 UTC (crypto trades 24/7, but quiet book near daily reset) — arbitrary but fixed;
coder may adjust the minute. Interpreter: `resolve_python.sh` (Rule 1d) — NEVER bare
`python3` (US-163). If a tighter "live tail" in the store is later wanted, bump to
`0 * * * *` hourly; that is a one-line cron change, not a redesign.

---

## 3. Read path (backtest + paper consumer)

### 3.1 Primary same-venue read

New unified reader in `hl_bar_store.py` (one entry point, so the proxy caveat is
impossible to bypass silently):

```python
class BarSource(str, Enum):
    HYPERLIQUID = "hyperliquid"
    OKX_PROXY   = "okx_proxy"   # pre-store gap ONLY — always labeled

def load_bars(ticker: str, timeframe: str, start_ts: int, end_ts: int,
              allow_proxy: bool = True) -> pd.DataFrame
    """Union-of-sources read for a backtest/paper window.
    1. Read store rows in [start_ts, end_ts)          -> source='hyperliquid'.
    2. If allow_proxy and store cover misses the LOW end (start_ts < coverage.min_ts):
       fetch OKX proxy bars for [start_ts, min_ts)    -> source='okx_proxy'.
    3. Concatenate, sort by ts, dedup on ts (store wins on collision).
    4. Drop source column into a labeled column 'source' so the caveat rides the data.
    Never fabricates, never silently mixes venues across an overlapping range; every
    proxy row carries source='okx_proxy'."""
```

Backtest + paper consumption: replace direct `intraday_provider` / OKX history reads in
the bar-level re-simulation (hostile_fills_strq_v2 and its drivers) with `load_bars(...)`.
The `data_source` metadata field in captured trades (capture_sweep_signals.py:346
`"hyperliquid"`) is ALREADY correct for live crypto and does not change.

### 3.2 OKX proxy fallback (explicit, labeled, bounded)

New module `scripts/data/okx_proxy.py` — the canonical labeled fallback (today only
ad-hoc orderbook/OI exist; candle history is added here):

```python
OKX_HOST = "https://www.okx.com/api/v5/market"
# Hyperliquid coin -> OKX perpetual instId. Explicit map; UNKNOWN ticker = skip + label.
HL_TO_OKX = {
    "BTC": "BTC-USDT-SWAP", "ETH": "ETH-USDT-SWAP", "SOL": "SOL-USDT-SWAP",
    # ... coder completes for the full universe; snake_case/1000x coins (kBONK/kPEPE/
    # kSHIB, FARTCOIN, PUMP, TRUMP) have NO reliable OKX equivalent -> map to None.
}
DEFAULT_BAR = "5m"

def fetch_okx_bars(ticker: str, timeframe: str, start_ms: int, end_ms: int) -> pd.DataFrame
    """GET /api/v5/market/history-candles?instId=...&bar=5m&after=&before= (paginate).
    Returns DataFrame[ts,open,high,low,close,volume] or EMPTY if unmapped/rate-limited.
    Raises NOTHING on data absence (returns empty) so the caller can label the gap."""
```

Symbol-mapping is the one genuinely fragile seam: Hyperliquid lists meme/1000x coins
with no OKX twin. Policy: unmapped ticker → empty proxy → the backtest window for that
ticker simply starts at the store floor (no fabricated bars). This is the honest
"sources differ per ticker" reality and must be surfaced, not papered over.

---

## 4. Retention estimate + authority timeline

Volume (5m, 288 bars/ticker/day, 35 tickers):

- bars/day total ≈ 288 × 35 ≈ 10,080
- bars/year ≈ 3.68M rows
- row ≈ 70-80 bytes (WITHOUT ROWID) + index ≈ ~100 bytes/row → **~0.4 GB/year** for 5m.
- 15m/1h/4h, if enabled later, add ≤ 1/3 of that (coarse intervals); negligible.
- SQLite/WAL handles this comfortably; no year-partitioning needed (< 50M rows/file).

Point of authority (explicit, per the "46-day OKX proxy" caveat):

- Day 0 (first run): store seeds ~17 days of same-venue 5m and is immediately
  authoritative for any window ≤ ~17 days ending now.
- Day N: store floor = day-0 (minus the ~17d backfill), growing forward. The pre-store
  gap is a FIXED width (everything before day-0); the fractions of any rolling window
  served by proxy shrink monotonically.
- ~Day 29 (46 − 17): the store ALONE covers the full 46-day window the prior OKX
  re-simulation used — the "46-day OKX proxy" caveat reaches zero for that scope.
- ~Day 348: the store alone covers a full 1-year 5m window; proxy needed only for
  windows longer than 1 year starting from before day-0.

Rule of thumb to ship in the docs: same-venue authoritative for any window whose
length ≤ (17 days + store age). Every `load_bars()` result carries the labeled
`source` column so "how much of this window is proxy" is inspectable, never implicit.

---

## 5. Module layout (final repository shape)

```
scripts/data/
    hl_bar_store.py               # NEW — storage layer (schema, append, read, coverage)
    ingest_hl_bars.py             # NEW — daily ingestion entrypoint (cron)
    ingest_hl_bars_wrapper.sh     # NEW — cron wrapper (Rule 1d interpreter)
    okx_proxy.py                  # NEW — labeled OKX history fallback only
    intraday_provider.py          # UNCHANGED (live capture path)
    fetch_crypto_data.py          # UNCHANGED (1d deep history)
    fetch_6h_data.py              # UNCHANGED (6h via 2h resample)
    liquidity_heatmap.py          # UNCHANGED (orderbook/OI only)
scripts/hermes_config/universe.py # UNCHANGED (single source of truth)
```

Import direction is one-way and acyclic:
`ingest_hl_bars.py -> hl_bar_store.py + hermes_config.universe`
`okx_proxy.py` is standalone (no store import). `hl_bar_store.load_bars` imports
`okx_proxy` (stdlib + requests only, unit-testable independent of the pipeline).

---

## 6. Implementation order (each a green commit)

1. `hl_bar_store.py` — schema, append_bars (idempotent), upsert_state, last_ts,
   coverage, read_bars. Unit test: append same window twice → 2nd inserts 0.
2. `ingest_hl_bars.py` — fetch_candles, incremental_window, ingest_ticker,
   ingest_timeframe, main. `--dry-run` against live API (no DB write in dry-run).
3. `ingest_hl_bars_wrapper.sh` + cron entry (no_agent, resolve_python.sh). Run once
   manually; verify ~17d seed + ingest_state rows.
4. `okx_proxy.py` + `load_bars()` unified reader with `source` labeling. Unit test:
   window above store floor → 100% hyperliquid; window straddling floor → proxy rows
   labeled, no overlap.
5. Rewire the bar-level re-simulation readers to `load_bars()`.

Path-scoped commit each step; py_compile clean. No edits to trades.csv / journal /
publisher / universe.

## 7. Explicit non-goals

- No edits to intraday_provider, fetch_crypto_data, fetch_6h_data, liquidity_heatmap,
  universe.py, or any publisher/posting path.
- No re-fetch/backfill of PAST Hyperliquid 5m beyond the ~17d the endpoint retains —
  that history is gone; the proxy labels it rather than pretending to recover it.
- No parquet migration of the store; optional columnar snapshot export is future work.
- No change to live capture data_source (already "hyperliquid").
- 1d timeframe excluded from this job (already deep + already ingested).

END OF DESIGN.