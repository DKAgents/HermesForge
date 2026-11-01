# Architect Spec — US-179 (Funding/Basis Carry) + US-180 (Execution-Drag Fix)

Date: 2026-11-01
Author: Architect (HermesForge)
Status: DESIGN ONLY — no pipeline code, no posts, no cron, no .env touched. Awaiting sign-off.
Epic: EPIC-016 (Refactor the Alpha Pipeline) — the two P0 stories.
Scope: endpoint-level + function-level design, concrete enough for a coder to
implement without re-deriving. Every ambiguous threshold (the prompt's "sustained"
threshold, the wider-stop ratio) is RESOLVED to an explicit default below and
flagged at the point of decision.

---

## 0. Ground truth read (verified — do not re-derive)

Files read in full:
- 02-Backlog/Stories/US-179 / US-180 (the two stories)
- reports/backtester/backtester_reevaluation_report.md
- reports/backtester/backtester_fidelity_report_v3.md  (the -2.86 R stop / -1.79 R forensic finding)
- scripts/paper_trading/hostile_fills.py            (swing, daily)
- scripts/paper_trading/hostile_fills_strq.py       (STR-Q v1, 5m — the canonical re-sim model)
- scripts/paper_trading/hostile_fills_strq_v2.py    (STR-Q v2, 5m — experimental "limit-price" variant)
- scripts/paper_trading/pnl_accounting.py           (US-164 shared accounting)
- scripts/gauntlet/g3_gate.py                       (US-174 mandatory promotion gate)
- scripts/gauntlet/fee_source.py                    (US-165 dynamic venue fees)
- scripts/gauntlet/cost_adjuster.py                 (compute_cost_drag, MIN_RISK_PCT=0.5%)
- scripts/gauntlet/funding_state.py                 (PROP-001 funding math — 8h framing)
- scripts/gauntlet/position_manager.py              (drawdown/cluster/headroom; no 1% notional cap here)
- scripts/data/hl_bar_store.py + ingest_hl_bars.py  (US-177 same-venue bar store)
- scripts/data/fetch_hyperliquid_metrics.py         (existing funding-history fetcher — TTL parquet cache)
- scripts/hermes_config/universe.py                 (CRYPTO_UNIVERSE, 35 tickers)

LIVE API PROBES (this design, read-only, no state written):

1. `POST https://api.hyperliquid.xyz/info {"type":"fundingHistory","coin":"BTC","startTime":<ms>}`
   Response = list of `{ "coin": str, "fundingRate": "<decimal HOURLY rate>",
                           "premium": "<signed decimal>", "time": <int ms epoch> }`.
   - One entry per HOUR (500 entries spanned 499 h — funding settles hourly).
   - `fundingRate` is the **native HOURLY** rate as a decimal string (observed
     BTC = "0.0000125" = 0.00125%/hr ≈ 10.95%/yr when premium is negative — i.e.
     the interest floor).
   - Capped at **500 entries/call**, ascending from `startTime`. PAGINATION =
     walk forward: `next_startTime = last_returned.time` until you reach `now`.
   - Deep retention CONFIRMED: a 400-day-back probe returned data (9599.8 h ago).
     ~21 days per 500-entry call, so a 1-year backfill ≈ 18 calls/coin.

2. `POST {"type":"metaAndAssetCtxs"}` → `[meta, assetCtxs]`:
   - `meta` = `{ "universe": [{name, szDecimals, maxLeverage, marginTableId, ...}],
                    "marginTables": [...], "collateralToken": <int> }`
     NOTE: `universe[i]` is asset CONFIG only — it does **not** carry `funding`.
   - `assetCtxs` = list indexed IDENTICALLY to `meta.universe`, each entry
     `{ "funding": "<current HOURLY rate>", "premium": "...", "openInterest": "...",
        "prevDayPx": "...", "dayNtlVlm": "...", "oraclePx": "...", "markPx": "...",
        "midPx": "...", "impactPxs": [...], "dayBaseVlm": "..." }`.
   - CURRENT funding for coin X = `assetCtxs[ idx_of_X_in_universe ]["funding"]`.
   - CURRENT basis = `(markPx - oraclePx) / oraclePx` (perp mark vs spot oracle).

DEFECTS FOUND DURING INVESTIGATION (flag, not in scope of these stories but must be
logged; do NOT silently "fix" here):

D1. `fetch_hyperliquid_metrics.py:198-206` compares the HOURLY `funding_rate`
    (≈1e-5) against 8h-style thresholds (`>0.0005`, `< -0.0002`) and comments
    "Hyperliquid funding is per-8h". The comparison is ~40x off. This is the exact
    unit confusion US-179's threshold section resolves.

D2. `fetch_hyperliquid_metrics.py:109-111` reads `ctx.get("oraclePrice")`,
    `ctx.get("markPrice")`, `ctx.get("prevDayFunding")`. The real fields are
    `oraclePx` / `markPx` / (no `prevDayFunding` field — it is `prevDayPx`).
    Result: `oracle_price`/`mark_price` are ALWAYS 0 today → OI-USD conversion
    (`oi_usd = oi * mark`) is silently 0. Log; do not fix here (path-scoped work).

D3. There are THREE copies of `check_entry_hostile`/`check_exit_hostile`
    (hostile_fills.py, hostile_fills_strq.py, hostile_fills_strq_v2.py). US-164
    consolidated the ACCOUNTING primitives but NOT these fill-choice functions.
    `hostile_fills_strq_v2.py` already fills at the *signal price* (not bar open)
    but STILL uses trade-through trigger + taker fee. US-180 supersedes that
    half-fix; see §2.6 for the retire-vs-align decision.

Import direction (acyclic), mirroring US-177:
  ingest_hl_funding.py -> hl_funding_store.py + hermes_config.universe
  funding_carry.py -> hl_funding_store.py + fee_source (+ g3_gate import for promotion)
  pnl_accounting.py, hostile_fills*.py  (no new cross-imports added by US-180)

---

# PART 1 — US-179: FUNDING / BASIS CARRY (delta-neutral crypto)

## 1.1 Data layer

### 1.1.1 Endpoint schemas (authoritative, verified)

Funding history (hourly, append-able, deep):

    POST https://api.hyperliquid.xyz/info
    body  {"type":"fundingHistory","coin":<name>,"startTime":<ms epoch>}
    resp  [ {"coin":<str>, "fundingRate":"<str decimal>", "premium":"<str signed>",
             "time":<int ms>}, ... ]          # <= 500 entries, ascending by time

Current snapshot (funding + basis + OI):

    POST https://api.hyperliquid.xyz/info
    body  {"type":"metaAndAssetCtxs"}
    resp  [ meta, assetCtxs ]
          meta = {"universe":[{name,...}], "marginTables":[...], "collateralToken":int}
          assetCtxs[i] = {"funding","premium","openInterest","oraclePx","markPx",
                          "midPx","impactPxs","prevDayPx","dayNtlVlm","dayBaseVlm"}

### 1.1.2 Local funding store (NEW — mirror hl_bar_store patterns)

Reuse the US-177 design idioms (SQLite, stdlib-only, `INSERT OR IGNORE` on a
composite PK, WAL, high-water-mark incremental append). This is the BACKTEST path
(deep append history). `fetch_hyperliquid_metrics.py`'s parquet TTL cache remains the
LIVE-signal path (current funding only) and is NOT changed.

New module `scripts/data/hl_funding_store.py` (stdlib only: sqlite3, pathlib, pandas
for read). One DB, single table (funding is one time-series, not timeframe-partitioned):

```python
STORE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_funding"
DB_NAME   = "funding.db"
PRAGMAS   = ("PRAGMA journal_mode=WAL;", "PRAGMA synchronous=NORMAL;",
             "PRAGMA foreign_keys=ON;")
FUNDING_PAGE = 500          # HL cap per fundingHistory call

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

def db_path() -> pathlib.Path                       # STORE_DIR / DB_NAME
def open_store() -> sqlite3.Connection               # open+create, PRAGMAs, DDL idempotent
def append_funding(conn, coin: str, rows: list[dict]) -> int
    """INSERT OR IGNORE keyed (coin,time). rows = [{time:int ms, funding_rate:float,
    premium:float}]. Idempotent (re-fetch overlap inserts 0). Commit inside; rollback
    on error (atomic). Returns count of NEW rows."""
def upsert_state(conn, coin: str, last_ts: int, last_run: str) -> None
def last_ts(conn, coin: str) -> int | None
def coverage(conn, coin: str) -> dict               # {'coin','min_ts','max_ts','n'}
def read_funding(coin: str, start_ts: int|None=None,
                 end_ts: int|None=None) -> pd.DataFrame
    """DataFrame[time, funding_rate, premium] ascending in [start_ts, end_ts)."""
```

Ingestion module `scripts/data/ingest_hl_funding.py` + `ingest_hl_funding_wrapper.sh`
(cron, Rule 1d `resolve_python.sh` interpreter — NEVER bare `python3`):

```python
def fetch_funding_page(coin: str, start_ms: int,
                       end_ms: int | None = None) -> list[dict]
    """POST fundingHistory; raise on HTTP!=200 (after 429/5xx backoff like
    ingest_hl_bars.fetch_candles); return [] on empty. Parse to
    {time:int, funding_rate:float, premium:float} (time = 'time' ms, rate=float(fundingRate))."""

def paginate_funding(coin: str, from_ms: int, to_ms: int) -> list[dict]
    """Walk forward: page = fetch_funding_page(coin, start); if len(page)==FUNDING_PAGE,
    start = page[-1]['time'] (+1ms) and repeat until page covers to_ms or returns
    short. Merge + dedup on time (ascending)."""

def incremental_window(conn, coin: str) -> tuple[int, int]
    """(start_ms, end_ms). First run (last_ts None): start = now - FIRST_RUN_BACKFILL_DAYS
    (default 400 — deep retention confirmed). Subsequent: start = last_ts - OVERLAP_MS
    (2h overlap), end = now."""

def ingest_coin(conn, coin: str) -> dict      # paginate + append_funding + upsert_state
def ingest_all(universe: list, dry_run: bool=False) -> dict
def main() -> int                             # argparse --dry-run --coins; exit non-zero on hard fail
```

Constants: `FIRST_RUN_BACKFILL_DAYS = 400`, `FUNDING_OVERLAP_MS = 2*3600*1000`.
Cron shape mirrors US-177 (`no_agent`, script wrapper, daily, `deliver: local`).
Volume: 24 rows/coin/day × 35 coins ≈ 840 rows/day ≈ 0.3M rows/year — trivial.

## 1.2 Unit normalization (resolves the /8h vs /h ambiguity)

The research cites thresholds per **8h** (Binance convention): "stable 0.005–0.02%/8h
→ 8–18%/yr"; "sustained 0.05–0.1% compounds higher". Hyperliquid funds **hourly**, and
`fundingRate` is the HOURLY fraction. The codebase already carries an 8h framing
(funding_state.py, execution_sim.py) that is NOT directly comparable to the endpoint.

CANONICAL UNIT (binding): **Annualized APR**, converted to/from the endpoint's HOURLY
fraction. This is venue-independent and directly comparable to the "8–18%/yr" reference:

    APR = hourly_rate * 8760            (8760 = 365 * 24)
    hourly_rate = APR / 8760
    8h-equivalent (for reading the research) = hourly_rate * 8 = APR / 1095

Two pure helpers live in `funding_carry.py` (NOT in funding_state.py — that module keeps
its PROP-001 8h semantics untouched):

    def hourly_to_apr(rate_hourly: float) -> float   # rate * 8760
    def apr_to_hourly(apr: float) -> float           # apr / 8760

FLAG + RESOLUTION: the research's "0.005–0.02%/8h → 8–18%/yr" does not reconcile under
simple annualization (0.005%/8h ≈ 5.5%/yr; 0.02%/8h ≈ 21.9%/yr). I resolve this by
treating 8% and 18% as the **canonical APR band-ends** and NOT re-deriving from the
/8h numbers. Every threshold below is stated in APR with its machine HOURLY fraction.

## 1.3 Signal — sustained elevated funding (exact thresholds)

All defaults are module constants in `scripts/gauntlet/funding_carry.py` (flag: tunable,
validated in the backtest). "Sustained" is a rolling-window statistic over N=24
consecutive HOURLY observations — never a single reading.

```python
FUNDING_WINDOW_HOURS      = 24      # rolling window length (hourly obs)
FUNDING_SUSTAIN_FLOOR_APR = 0.08    # 8%/yr  = hourly 9.132e-6  (bottom of "decent" band)
FUNDING_ELEVATED_APR      = 0.18    # 18%/yr = hourly 2.055e-5  (top of "decent" band → boost tier)
FUNDING_POSITIVE_FRACTION = 0.75    # >= 18 of 24 trailing hours must be funding > 0
```

ENTRY gate — ALL FOUR must hold (and must hold at the moment of rebalancing):

    S1  mean(funding_rate[last W hours]) >= apr_to_hourly(FUNDING_SUSTAIN_FLOOR_APR)
    S2  count(funding_rate > 0 in window) >= FUNDING_POSITIVE_FRACTION * W
        (S2 is what turns "a single high spike" into a non-signal: one 0.5%/hr spike
         plus 23 ~0 hours → mean ~0.02%/hr (~1.8%/yr) < S1, AND positive-fraction
         1/24 < 0.75 → rejected on both.)
    S3  current funding_rate > 0.0            (no imminent flip at entry)
    S4  cost_clears(mean_apr)                 (net-of-cost gate, §1.6.3)

BOOST tier (confidence multiplier, mirrors the principal's "confluence = confidence"):
if the rolling MEAN apr >= FUNDING_ELEVATED_APR, the signal is High-confidence
(normal band = Medium). Note: the research's "0.05–0.1%/8h compounds higher" is
~55–110%/yr — that is the extreme-flip-risk regime, NOT a boost. Codify as a WARNING
flag (`extreme_funding=True`): carry is highest-yield but rate-flip/basis-widen risk
dominates → do NOT size up; if anything reduce. (Reference balance: flag, not gate.)

Function signature:

```python
def funding_window_signal(series: pd.DataFrame) -> dict
    """series: DataFrame[time, funding_rate, premium] ascending (>= W rows).
    Returns {sustained: bool, elevated: bool, extreme: bool,
             mean_apr: float, current_apr: float, positive_fraction: float,
             cost_clears: bool, reasons: list[str]}."""
```

## 1.4 Construction — delta-neutral long-spot / short-perp

Canonical leg pair (funding > 0 branch): **long spot + short perp**. You are short the
crowd's leverage demand; when funding > 0 (longs pay shorts) the short perp RECEIVES
funding each hour; the long-spot leg zeroes the delta. Borrow/basis is captured as the
perp premium converges toward spot each settlement.

    if mean_apr > 0  (positive-funding carry):  LONG spot, SHORT perp   (receive funding)
    if mean_apr < 0  (negative-funding carry):  LONG perp, SHORT spot   (receive funding)

FLAG + RESOLUTION (asymmetry): Hyperliquid spot does not support shorting for most of
the universe (only longs), and spot depth is thin outside BTC/ETH. Therefore the
strategy is **asymmetric by construction**: the positive-funding branch (long spot /
short perp) is the PRIMARY implementable carry; the negative-funding branch (requires
short spot) is OUT OF SCOPE / opportunistic. Do not model a symmetric strategy that
cannot be executed.

"HL-native equivalent" for coins without spot: short perp + delta-hedge via a BTC-perp
overlay (short the coin's BTC-beta), accepting an explicit residual delta. This is a
DIFFERENT risk profile (beta-mismatch, not true neutral) and is SECONdary; if the
residual |net delta| > DELTA_CAP the coin is INELIGIBLE for carry (skip, label).

Carry P&L accounting (per entry-to-exit episode), fees via fee_source (US-165):

    funding_pnl    = sum over hours held of (sign * funding_rate * notional)
                     sign = +1 when short perp (receive positive funding)
                            -1 when long  perp
    basis_pnl      = realized (spot exit-entry) + (perp entry-exit)  [≈ premium convergence]
    execution_cost = entry_cost + exit_cost  (both legs, §1.6.3)
    net_carry      = funding_pnl + basis_pnl - execution_cost

Note the delta-neutral sum (spot + perp) of MARK-to-market is ~0 by construction; the
carry edge is funding_pnl + basis convergence, net of friction. `1R` is defined as the
basis-risk budget (§1.5) so the promotion gate (G3) is directly applicable.

## 1.5 Position size, capacity, and the 1% rule

The 1% rule ("never risk >1% of capital on one idea") applies to the RESIDUAL risk of a
delta-neutral position, which is basis-widening / rate-flip — NOT notional. Because the
hedge removes directional risk, notional can exceed 1% of capital while the basis-risk
budget stays at 1%. This is the legitimate way the carry scales, bounded by three rails:

```python
CAPITAL_RISK_BUDGET = 0.01   # 1% of capital = max adverse-basis loss (the "1R")
KILL_BASIS_BPS      = 50.0   # 0.50% basis-widening stop (defines "1R" distance)
GROSS_NOTIONAL_CAP  = 0.20   # hard safety rail: notional <= 20% of capital
OI_CAPACITY_FRAC    = 0.02   # notional <= 2% of coin open interest (self-dampening)
DELTA_CAP           = 0.05   # |net delta|/notional <= 5% (else ineligible)
```

```python
def size_position(capital: float, kill_basis_bps: float,
                  open_interest_usd: float, eligible: bool) -> dict:
    """Returns {notional, basis_risk_usd, size_capped, cap_reason}.
    notional = min( (CAPITAL_RISK_BUDGET*capital) / (kill_basis_bps/1e4),
                    GROSS_NOTIONAL_CAP*capital,
                    OI_CAPACITY_FRAC*open_interest_usd )
    basis_risk_usd = notional * kill_basis_bps/1e4   # must be <= 1% capital.
    eligible=False -> {notional: 0, ... 'ineligible: residual delta'}."""
```

Capacity is therefore EXPLICITLY self-dampening: the OI-fraction rail is the binding one
for thin coins (you cannot short-funding more than ~2% of OI without driving funding
toward zero — the exact rate-flip you are trying to avoid). Actual OI-USD comes from
`assetCtxs[idx].openInterest * markPx` (NOT the broken `fetch_hyperliquid_metrics`
OI-USD in D2 — use `markPx`, not `markPrice`).

## 1.6 Risk constitution — the two documented killers + cost

### 1.6.1 Rate-flip kill

Funding is the whole edge; a flip to negative inverts it (you start PAYING). Hard exit:

```python
FLIP_EXIT_FLOOR     = 0.0     # current hourly funding <= 0 -> exit BOTH legs now
DERISK_DECAY_APR    = 0.04    # rolling-mean APR < 4%/yr while still positive -> DE-RISK
                              # (scale down / stop adding); a flip usually follows decay.
```

    rate_flip(series)  -> bool     # current funding_rate <= FLIP_EXIT_FLOOR
    funding_decaying(series) -> bool # rolling mean_apr < DERISK_DECAY_APR

### 1.6.2 Basis-widening kill (the stop)

The premium (perp − spot) is both the income source and the risk distance. If the perp
premium WIDENS against the short-perp leg (perp rises further above spot), the short
perp's mark-to-market loss grows while funding keeps paying — the classic "got paid, lost
the position" death. Monitor `basis_bps = (markPx - oraclePx)/oraclePx * 1e4`:

```python
def basis_widen(perp_mark: float, spot_oracle: float) -> float:
    """basis in bps = (perp_mark - spot_oracle)/spot_oracle * 1e4 (signed)."""

EXIT when |basis_bps against the short-perp direction| >= KILL_BASIS_BPS (50 bps).
```

Live monitoring uses `assetCtxs` markPx/oraclePx. Backtest uses the fundingHistory
`premium` column (the hourly premium IS the historical basis proxy — no separate basis
table needed for backtest).

### 1.6.3 Execution cost gate (sub-0.005% funding eats the carry)

Cost-clearing is a HARD sub-gate (S4). The carry pays two-leg friction, amortized over a
minimum hold:

```python
MIN_HOLD_HOURS        = 168        # 1 week
CARRY_ROUND_TRIP_BPS  = 24.0       # conservative two-leg taker (2 x get_round_trip_bps(crypto)=12)
                                   # = 12.0 if BOTH legs use maker/limit fills (US-180)

def cost_clears(mean_apr: float, cost_bps: float = CARRY_ROUND_TRIP_BPS,
                hold_hours: float = MIN_HOLD_HOURS) -> bool:
    """mean_apr * (hold_hours/8760) >= cost_bps/1e4."""
```

DERIVATION (why the floor must be COST-clearing, not the "8%/yr" gross band) — expose
this in the docs, it is a real finding, not a placeholder:

    break-even APR (taker, 24 bps, 1 wk) = 0.0024 / (168/8760) = 12.5%/yr
    break-even APR (maker, 12 bps, 1 wk) = 0.0012 / (168/8760) =  6.3%/yr
    break-even APR (maker, 12 bps, 2 wk) = 0.0012 / (336/8760) =  3.1%/yr

So the "8%/yr decent carry" is only net-positive if the legs fill as MAKER (US-180's
limit entries/targets) — which is exactly why US-179 and US-180 are coupled, and why
US-180 is a P0 dependency of the carry edge, not a cosmetic optimization. With taker
fills the net floor is ~12.5%/yr (the elevated band), making the 8% band uneconomic.

CONCLUSION (binding default): the S1 floor stays at 8%/yr (gross "interesting" band), but
S4 (cost gate) is the binding entry floor, and the validation MUST report the carry with
both fee assumptions (taker-round-trip and maker-round-trip) so the maker-fill path's
viability is explicit.

## 1.7 Validation

Module `scripts/gauntlet/funding_carry.py` (new) owns the backtest + G3 wiring.

```python
def simulate_carry(funding: pd.DataFrame, basis: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Hourly walk. At each hour: if not in position and funding_window_signal() passes
    (S1-S4) -> enter (record entry cost). While in position: accrue funding_pnl; check
    rate_flip / basis_widen / decay -> exit (record exit cost). Returns one row per
    episode: coin, entry_ts, exit_ts, exit_reason, funding_pnl, basis_pnl, execution_cost,
    net_carry, net_r (net_carry / basis_risk_budget), regime_label."""

def carry_g3_record(episodes: pd.DataFrame) -> dict:
    """Apply US-174 gate semantics to carry episodes using net_r (1R = basis-risk budget).
    optimistic  = net_r with zero execution_cost (gross carry)  [diagnostic only]
    realistic   = net_r with maker-fill cost (12 bps)
    pessimistic = net_r with taker-fill cost (24 bps) + basis-gap on the kill exit
                  (exit basis widened by +1 tick beyond KILL_BASIS_BPS)
    Return {n, optimistic_mean_r, realistic_mean_r, pessimistic_pf, passed}. Feed the
    REALISTIC mean R and PESSIMISTIC PF through g3_gate.assert_g3_gate(...) using the
    carry's own R unit. Frame caveat: G3's per-trade R was built for directional R;
    here "R" is redefined as basis-budget R so n>=10, mean R>0, PF>1, decay>=0.6 still
    mean what they mean. Flag this R-unit mapping explicitly in the promotion record."""

def partition_regime(episodes: pd.DataFrame, btc_30d_ret: pd.Series) -> dict:
    """Partition episodes by BTC trend regime: bull (30d ret > +2%), bear (< -2%),
    neutral (else). Report net_r mean/PF per regime. Funding carry is structurally short
    the crowd: expect positive funding to concentrate in bull-leverage regimes and
    basis-widening losses to concentrate in violent bull extensions."""
```

The G3 gate (US-174) is mandatory and fail-closed: NO promotion to LIVE/WATCH unless the
carry passes realistic-mean-R>0, pessimistic-PF>1, n>=10, edge-decay>=0.6, AND the net
edge survives bull/bear/neutral partitioning (no single regime carrying the whole edge).

Backtest data source: `hl_funding_store.read_funding()` (deep append history) for funding
+ premium (basis proxy). Regime data: BTC 1d bars already ingested by fetch_crypto_data.py.

---

# PART 2 — US-180: EXECUTION-LAYER DRAG FIX

## 2.0 Diagnosis (the -2.86 R stop / -1.79 R mean — from v3)

The bar-level re-sim (v3) pinned the drag to three structural defects in the fill
CHOICE, all inside the hostile model:

    (i)   trade-through entry fills at the BAR OPEN. For a long, the bar that "trades
          through" the swept level has its open ABOVE the level → you buy the level late
          and high (adversarial selection: you only fill after the reversal ends).
    (ii)  tight stops (STR-Q ~0.1–0.3%) make one tick of slippage + both-side taker a
          large fraction of R → "−1 R nominal → −2.86 R actual".
    (iii) worst-print stops + trade-through targets turn a would-be winner into a
          missed fill + time-stop loss.

The fix changes fill CHOICE, not the cost MATH. US-164..168 correctness (entry slippage
via `_compute_r` numerator, `_apply_taker_fee` adverse direction, dynamic `fee_source`
venue fees, `_reconcile_signal_dedup`/dedup, `_worst_print`/`_bar_touches`/`_trades_through`
primitives, DEGENERATE_RISK_FLOOR self-guards) is PRESERVED BYTE-FOR-BEHAVIOR. The only
things that change are (a) the stop VALUE, (b) the entry TRIGGER/price, (c) the maker-vs-
taker bps chosen per leg.

## 2.1 (a) Wider stops — lower fee-per-R, no risk increase

The fee-per-R fraction is `round_trip_bps/1e4 / stop_pct`. It depends ONLY on stop_pct.
Widening the stop lowers fee-per-R without touching notional (the dollar-risk cap is
enforced by the position sizer, which is OUTSIDE the hostile model). The hostile model is
R-unit-only and does not size, so "no risk increase" is satisfied by construction: widen
only grows the R DENOMINATOR (distance), shrinking both |win R| and |loss R| and shrink
fee-per-R — the honest effect of risking more distance for the same setup.

NEW in `pnl_accounting.py` (additive — does NOT alter any existing function):

```python
STOP_WIDEN_FACTOR = 2.0     # flag: default; sensitivity set {1.5, 2.0, 3.0} in validation

def widen_stop(entry: float, stop: float, direction: str, factor: float) -> float:
    """Widen stop distance by `factor` (>= 1.0) away from entry. Never shrinks a stop.
    long  -> entry - |entry-stop| * factor
    short -> entry + |entry-stop| * factor
    Guard: entry<=0 or stop<=0 or factor<1.0 -> return `stop` unchanged."""
```

Preserved invariants (explicit): `MIN_RISK_PCT` (cost_adjuster, 0.5%) and
`DEGENERATE_RISK_FLOOR` (pnl_accounting, 0.10%) are FLOORS (minimums). Widening moves
risk AWAY from them (upward), never below — so neither floor changes and "no risk
increase" is not violated by them. The 1% dollar cap is applied in the sizer path
(notional = risk_budget / widened_stop_pct → for the same 1% dollar budget you hold
FEWER units). That sizer path is NOT part of this diff; flag as the companion change.

## 2.2 (b) Limit entries at the swept level (not chasing trade-through)

Current (all three files): `if _trades_through(row, entry_price, side): fill=row["open"] + taker`.
Redesign: fill at the LIMIT (the swept level) when price TRADES BACK TO it; maker fee;
else SKIP (never chase).

    trigger  : _bar_touches(row, entry_price)     # bar range contains the level (price came back)
    fill     : entry_price                         # the limit itself, NOT row["open"]
    fee      : maker  (fee_source.get_maker_bps)   # limit = maker

This removes (i): you no longer pay the reversal's adverse open; you either fill at the
level or skip. `_bar_touches` is already imported and unchanged.

## 2.3 (c) Market-vs-limit exit choice

    STOP   exit -> MARKET: worst print + taker      (UNCHANGED — stop must fill)
    TARGET exit -> LIMIT : fill at target + MAKER   (trigger `_trades_through` unchanged;
                       only the fee changes taker->maker)
    TIME   exit -> MARKET: worst print + taker      (UNCHANGED; conservative default)
                       (flag: optional maker-at-close variant, OFF by default)

Rationale: a resting limit at target is a maker fill (posts liquidity) → 1.5 bps vs
4.5 taker; a stop is a market order → worst print + taker. This is exactly "limit when
liquidity allows, market when the stop must fill."

## 2.4 Exact function-level diff (which functions, what changes)

NOTE on the maker fee and "taker fees unchanged": `_apply_taker_fee(price, direction,
is_entry, taker_bps)` already takes the fee as a `taker_bps` parameter and applies the
US-166 adverse-direction logic. Passing `fee_source.get_maker_bps(...)` to that SAME
function yields the maker fee with identical adverse-direction math. So the cost MATH
(fee magnitude source, direction fix, self-guards) is untouched; only the bps VALUE per
leg is chosen by fill type. Do NOT rename the param (avoid churn); add a one-line comment
that `taker_bps` is really "leg bps (taker or maker)".

FILES THAT CHANGE (fill-choice functions — still duplicated post-US-164):

  scripts/paper_trading/hostile_fills.py         (swing, daily)
  scripts/paper_trading/hostile_fills_strq.py    (STR-Q v1, 5m — canonical re-sim)
  scripts/paper_trading/hostile_fills_strq_v2.py (see §2.6 retire/align decision)
  scripts/paper_trading/pnl_accounting.py        (ADDITIVE: widen_stop + STOP_WIDEN_FACTOR)

check_entry_hostile(...)  [all three files] — change ONLY the fill branch:

  BEFORE:
      taker_bps = fee_source.get_taker_bps(...)
      if _trades_through(row, entry_price, side):
          fill_price = _apply_taker_fee(float(row["open"]), direction, is_entry=True, taker_bps=taker_bps)

  AFTER:
      maker_bps = fee_source.get_maker_bps(trade.get("asset_class", ...))
      if _bar_touches(row, entry_price):                       # (b) trades-back-to-level
          fill_price = _apply_taker_fee(float(entry_price), direction, is_entry=True, taker_bps=maker_bps)
          return {..., "fill_reason": "limit fill at swept level", "fill_mode": "limit", "fee_bps": maker_bps}

  (strq versions keep their CONFIRMATION_BARS lag and _find_signal_bar; swing keeps t+1.
   The trigger condition and fill price change; everything else — including the
   "no bar traded back → filled:False (skip)" tail — stays.)

check_exit_hostile(...)  [all three files] — change ONLY the target leg fee:

  BEFORE (target branch):
      exit_price = float(target_price)
      exit_price = _apply_taker_fee(exit_price, direction, is_entry=False, taker_bps=taker_bps)

  AFTER:
      exit_price = _apply_taker_fee(float(target_price), direction, is_entry=False,
                                    taker_bps=maker_bps)       # maker = limit target

  (Stop + time branches UNCHANGED — still worst print + taker. Add `maker_bps =
   fee_source.get_maker_bps(...)` once at the top of check_exit_hostile.)

run(...)  [hostile_fills.py + hostile_fills_strq.py + _v2] — the WIDENING is caller-side
data transformation (check_exit_hostile signature and _compute_r formula both UNCHANGED):

  BEFORE (strq):
      hostile_trade = {**trade, "entry_price": hostile_entry_price}
      exit_result   = check_exit_hostile(hostile_trade, bars, entry_bar_idx)
      hostile_r = _compute_r(paper_entry=paper_entry, paper_stop=paper_stop, ...)

  AFTER:
      paper_entry  = float(trade["entry_price"])
      paper_stop   = float(trade["stop_price"])
      widened_stop = widen_stop(paper_entry, paper_stop, trade["direction"], STOP_WIDEN_FACTOR)
      hostile_trade = {**trade, "entry_price": hostile_entry_price, "stop_price": widened_stop}
      exit_result   = check_exit_hostile(hostile_trade, bars, entry_bar_idx)
      hostile_r = _compute_r(paper_entry=paper_entry, paper_stop=widened_stop,
                             direction=..., hostile_entry_price=..., exit_price=...)

  (Swing (hostile_fills.py) is the same but check_exit_hostile has no entry_bar_idx; the
   widening + _compute_r paper_stop=widened_stop change is identical. The setup_risk_pct /
   DEGENERATE_RISK_FLOOR degenerate check MUST use the WIDENED stop so the scoreability
   test matches the risk actually modeled.)

COST MATH PRESERVED (verbatim, do not touch): `_apply_taker_fee` body, `_compute_r`
body (entry slippage in numerator / fixed-risk denominator), `_adversarial_cost_drag`,
`_paper_r`, `_worst_print`, `_trades_through`, `_bar_touches`, `_authoritative_close`,
`_close_outcome`, `_reconcile_signal_dedup`, `DEGENERATE_RISK_FLOOR`, and all
`fee_source.*`. Only the bps ARGUMENT value (taker vs maker) and the stop VALUE change.

## 2.5 Acceptance measurement (quantify the drag reduction)

Re-run `hostile_fills_strq.py` (force rescore) and `hostile_fills.py` under the new rules
and produce the comparison against the v3 baselines. The coder must report:

    metric                    v3 baseline   new (STOP_WIDEN_FACTOR=2.0)
    STR-Q avg R/trade          -1.591
    STR-Q median stop-out R    -2.86 (stop from -1 R nominal; derive the exact v3 median
                                          stop-out R in the run, don't assume -2.86 is the median)
    STR-Q win rate             24.7%
    fee-per-R (crypto, stop%)  report as a table per stop-width

Also produce a small sensitivity table over STOP_WIDEN_FACTOR ∈ {1.5, 2.0, 3.0} so the
2.0 default is justified by data, not assertion. Success = a measurable reduction in the
per-stop drag and in avg-R magnitude (toward coin-flip-minus-fee ~ -0.3R), with n and
t-stat reported.

## 2.6 v2 retirement/alignment (flag, decide at implementation)

`hostile_fills_strq_v2.py` partially implements the (b) fix (limit-PRICE fill) but keeps
trade-through + taker. US-180 supersedes it. DECISION (recommended): implement US-180 in
the two canonical files (hostile_fills.py, hostile_fills_strq.py), then RETIRE v2
(delete or a single commit marking it superseded + removing its cron/reference) — do NOT
maintain a third diverging copy. Confirm with the user before deleting; the file is
currently unreferenced by the v3 re-sim path.

## 2.7 Explicit non-goals (US-180)

- No change to position sizing / the 1% dollar cap (companion sizer change flagged, not implemented here).
- No change to `_apply_taker_fee`/`_compute_r`/`fee_source` bodies.
- No re-fetch of bars; this uses the SAME bars the current re-sim uses.
- No change to trades.csv / trade_journal.jsonl / publisher / dedup.

---

# PART 3 — Cross-cutting: resolved ambiguities, flags, ordering

## 3.1 Ambiguities RESOLVED (with the default)

  A1 "sustained" threshold  -> rolling W=24h mean APR >= 8% AND >=75% of hours positive (§1.3).
  A2 "wider-stop ratio"     -> STOP_WIDEN_FACTOR = 2.0, sensitivity {1.5,2.0,3.0} (§2.1).
  A3 funding units (/8h vs /h) -> canonical APR; hourly = APR/8760 (§1.2); the live
                               codebase's 8h framing is the exact source of D1.
  A4 "single high reading not a signal" -> enforced by S2 (positive-fraction) + S1 (mean) (§1.3).
  A5 net carry floor       -> cost-clearing gate S4, ~12.5%/yr (taker) vs ~6.3%/yr (maker, 1wk)
                              (§1.6.3); the 8% band is net-positive only with maker fills.
  A6 negative-funding leg  -> out of scope (no HL spot shorting); asymmetric carry (§1.4).

## 3.2 Flags raised (not resolved here — need a decision)

  F1  D1/D2 (unit confusion + wrong field names in fetch_hyperliquid_metrics.py) — latent
      bugs outside these stories; log, fix in a path-scoped follow-up.
  F2  v2 retirement (§2.6) — needs user confirmation before delete.
  F3  G3 "R" unit re-mapping for a carry strategy (§1.7) — the promotion gate was built
      for directional R; the carry redefines 1R = basis-budget R. Documented, not silent.
  F4  `fundingHistory` `endTime` support — existing code passes it; this design paginates
      on `startTime` only. Coder should confirm `endTime` is honored or ignored and NOT
      rely on it for pagination.
  F5  Spot-leg depth/capacity — real capacity numbers need a live `assetCtxs` OI + spot
      depth probe; §1.5 gives the rails + formula, not a pre-computed per-coin capacity.

## 3.3 Implementation order (each a path-scoped green commit, py_compile clean)

  1. hl_funding_store.py (+ unit test: append same window twice -> 2nd inserts 0).
  2. ingest_hl_funding.py + wrapper + cron (no_agent, resolve_python.sh). Run once
     manually; verify deep backfill + ingest_state rows.
  3. funding_carry.py: unit-normalization helpers + funding_window_signal + cost_clears
     + size_position + rate_flip/basis_widen (unit-test the threshold math golden vectors).
  4. US-180: pnl_accounting.py widen_stop + STOP_WIDEN_FACTOR (pure, unit-test guard).
  5. US-180: check_entry_hostile / check_exit_hostile / run() diffs in hostile_fills.py +
     hostile_fills_strq.py (parity test: same inputs, only changed legs differ).
  6. simulate_carry + carry_g3_record + partition_regime; run the carry backtest on
     hl_funding_store history; feed g3_gate.assert_g3_gate.
  7. Re-run hostile re-sims (+v2 retirement per F2) and produce the §2.5 drag table.

No edits to trades.csv / journal / publisher / universe.py / live capture in any commit.

END OF DESIGN.