# Architect Spec — US-185 (Funding-Carry Reconstitution: Full-Universe Executable)

Date: 2026-11-01
Author: Architect (HermesForge)
Status: DESIGN ONLY — no pipeline code, no posts, no cron, no .env touched. Awaiting sign-off.
Epic: EPIC-016 (Refactor the Alpha Pipeline)
Scope: endpoint-level + function-level design, concrete enough for a coder to
implement without re-deriving. Every ambiguous threshold is RESOLVED to an
explicit default below and flagged at the point of decision.

Summary of what this spec fixes (the four defects US-179's independent validation
surfaced):
  1. Delta-neutral long-spot/short-perp was backtested on ~30 coins with NO liquid
     spot leg (the premise was false). Rebuild construction so EVERY non-delisted
     HL perp is tradeable — hedged where genuine spot exists, DIRECTIONAL elsewhere
     with the price risk modeled and gated.
  2. ~54% of net carry was a basis term concentrated in non-spot coins and sourced
     from the compressed fundingHistory `premium`. Decompose honestly: headline edge
     = FUNDING only; basis re-sourced from the REAL mark-oracle spread (assetCtxs).
  3. "1R" was $1,000 = 0.1% of capital (the 20% gross-notional rail silently shrank
     the risk unit while keeping the "R" label). Fix so 1R is an honest 1% of capital.
  4. `basis_widen` fired 2/313 times because it was fed the compressed `premium`,
     not the real mark-oracle basis. Re-source the stop.

---

## 0. Ground truth read (verified — do not re-derive)

Files read in full:
- 02-Backlog/Stories/US-185-Funding-Carry-Full-Universe.md
- reports/backtester/funding_carry_validation.md
- scripts/gauntlet/funding_carry.py
- scripts/gauntlet/funding_state.py
- scripts/data/ingest_hl_funding.py
- scripts/data/hl_funding_store.py
- scripts/data/fetch_hyperliquid_metrics.py
- scripts/hermes_config/universe.py
- 02-Backlog/Specs/architect_us179_180_spec.md (the prior design this corrects)

LIVE API PROBES (this design, read-only; run from scratch dir; no state written):

P1. `POST https://api.hyperliquid.xyz/info {"type":"metaAndAssetCtxs"}` → `[meta, assetCtxs]`
    - `meta.universe` = 235 perps TODAY; `meta.universe[i]` = asset CONFIG
      `{name, szDecimals, maxLeverage, marginTableId, ...}` (no funding, no px).
    - `assetCtxs` = 235 entries, INDEX-ALIGNED with `meta.universe`. Each:
      `{funding, openInterest, prevDayPx, dayNtlVlm, premium, oraclePx, markPx,
        midPx, impactPxs, dayBaseVlm}`.
    - Confirmed field names are `markPx` / `oraclePx` (NOT `markPrice`/`oraclePrice`
      as the buggy fetch_hyperliquid_metrics.py:109-111 reads → that code's
      `oracle_price`/`mark_price` are always 0 today; see flag F1).
    - `openInterest` is in BASE COIN UNITS; OI-USD = `openInterest * markPx`.
    - Verified current values: `funding` is the HOURLY decimal (BTC = "0.0000125" =
      the ~10.95%/yr interest floor); `premium` is a NEGATIVE impact-price premium
      (BTC = -0.0004506); the REAL mark-oracle basis for BTC = (77638-77672)/77672
      = -4.38 bps, which is NOT the same quantity as `premium`.

P2. `POST {"type":"spotMetaAndAssetCtxs"}` → `[spotMeta, spotAssetCtxs]`
    - `spotMeta = {universe, tokens}`. `tokens` = 511 token descriptors; each spot
      market's base/quote are token INDICES resolved through `tokens[index].name`.
    - `spotMeta.universe[i] = {name, tokens:[baseIdx, quoteIdx], index}`. The quote
      for the fiat pair is `USDC` (index 0).
    - CRITICAL FINDING: HL spot does NOT list the majors under their perp names.
      Major underlyings exist only as WRAPPED/BRIDGED spot variants with a name
      suffix or `U` prefix, and their spot depth is ~ZERO:
        BTC  → UBTC  (dayNtlVlm = **$25**), markPx ≈ 0.0000 (pre-tokenization)
        ETH  → UETH  (dayNtlVlm = **$0**)
        SOL  → USOL  (dayNtlVlm = **$0**)
        AVAX → AVAX0/UAVAX ($4.8k / $0), LINK → LINK0 ($0), AAVE → AAVE0 ($532),
        BNB → BNB0 ($233), TRX → TRX1 ($15.3k), ZEC → UZEC ($124k), XPL → UXPL ($2.6k)
    - The ONLY meaningfully liquid HL spot markets are HYPE-ecosystem native assets:
      WOW ($25.5M), NEKO ($16.6M), QQQ ($7.0M), GLD ($5.9M), QUANT ($4.8M),
      BUDDY ($1.5M), PURR ($0.6M) — none of which are CRYPTO_UNIVERSE majors, and
      HYPE itself is illiquid on HL spot (~$0-$85/day).
    - NET RESOLUTION of the "which coins have HL spot today" ambiguity: for the
      35-coin CRYPTO_UNIVERSE, delta-neutral long-spot/short-perp is NOT executable
      at meaningful size on HL spot for ANY of the majors today. It is executable
      only for a small set of HYPE-ecosystem names (partial list above), which are
      outside CRYPTO_UNIVERSE. Therefore the directional short-perp form is the
      LOAD-BEARING construction for the full (235-coin) universe — exactly what the
      principal asked for.

P3. `POST {"type":"fundingHistory","coin":X,"startTime":ms}` — as US-179 §1.1.1
    (verified earlier, unchanged): hourly `{coin, fundingRate, premium, time}`,
    500/call. RETENTION: fundingHistory is deep (~400d) and is the ONLY deep
    historical series. There is NO endpoint returning historical `markPx`/`oraclePx`
    — the real mark-oracle basis can only be accumulated GOING FORWARD (see §2.3).

Import direction (acyclic) — UPDATED for US-185:
  ingest_hl_funding.py -> hl_funding_store.py + hermes_config.universe      (unchanged)
  ingest_hl_assetctx.py -> hl_assetctx_store.py + hermes_config.universe   (NEW, §2.3)
  funding_carry.py -> hl_funding_store.py + hl_assetctx_store.py
                      + fee_source + g3_gate                                (UPDATED)
  (fetch_hyperliquid_metrics.py untouched in this story — its D2 field-name bug is
   F1, out of scope.)

---

# PART 1 — FULL-UNIVERSE EXECUTABLE CONSTRUCTION

## 1.1 Universe = every non-delisted perp (long AND short)

The full universe is `metaAndAssetCtxs` `meta.universe`, filtered to
`not isDelisted` (235 TODAY), NOT the 35-ticker CRYPTO_UNIVERSE. Every perp is
two-sided: funding > 0 pays shorts, funding < 0 pays longs. So "trade nearly all
HL assets long and short" is satisfied natively by the RECEIVING direction:

    funding > 0  ->  SHORT perp receives funding
    funding < 0  ->  LONG  perp receives funding
    funding ~ 0  ->  no carry (skip)

The negative-funding (long-perp) branch is structurally simpler than the
positive-funding branch's spot problem (no spot SHORT needed — you just go long the
perp), so it is fully executable across the whole universe. The positive-funding
(short-perp) branch is the one that needs a construction decision (§1.2-1.4).

## 1.2 Spot availability resolver (determines the execution form per coin)

New module-level function in `funding_carry.py` (data fed from a NEW cached
snapshot, §2.3). It maps a perp name to (a) whether a liquid HL spot leg exists and
(b) the wrapped-variant name if any:

```python
# funding_carry.py
SPOT_MIN_DAY_NTL_VLM_USD = 500_000.0   # spot leg must clear 24h USD notional [tunable]
SPOT_MAX_SPREAD_BPS      = 25.0        # spot mark-vs-mid spread cap            [tunable]

def resolve_spot_leg(perp_name: str, spot_snap: dict) -> dict:
    """spot_snap = one parsed spotMetaAndAssetCtxs result (§2.3 snapshot).
    Resolve whether `perp_name` has a tradeable HL spot hedge.
    Candidate names (exact first, then wrapped variants): {name}, {name}0, {name}1,
    U{name}.  (e.g. BTC -> BTC, BTC0, BTC1, UBTC.)
    Returns {available: bool, spot_name: str|None, day_ntl_vlm_usd: float,
             spread_bps: float, reason: str}.
    available = a candidate exists AND day_ntl_vlm_usd >= SPOT_MIN_DAY_NTL_VLM_USD
                AND spread_bps <= SPOT_MAX_SPREAD_BPS."""
```

FLAG + RESOLUTION (spot-variant naming): HL spot uses zero/suffix/`U`-prefix names
that are NOT algorithmically derivable from the perp name in general (e.g. `TAO1`,
`XMR1`, `CFX0`, `USOL`, `UETH`). The candidate list above is a best-effort cover;
the AUTHORITATIVE mapping is read live from `spotMetaAndAssetCtxs` each snap and
matched on token name, so it self-heals when HL adds/renames spot tokens. Do NOT
hardcode a static coin->spot map.

## 1.3 Execution-form dispatch (per coin, per funding sign)

```python
def dispatch_execution_form(funding_sign: float, spot: dict, in_universe: bool,
                            delisted: bool) -> str:
    """Returns one of:
      'skip'               delisted, or funding ~ 0 (no carry)
      'delta_neutral'      funding > 0 AND spot.available (long spot + short perp)
      'directional_short'  funding > 0 AND NOT spot.available (naked short perp)
      'directional_long'   funding < 0 (naked long perp; no spot short needed)
    Delta-neutral for funding < 0 would require SHORT spot, which HL does not
    support for the majors -> never dispatched (falls through to directional_long)."""
```

This is the heart of "do not reject non-spot coins": a coin WITHOUT liquid spot is
NOT skipped — it is routed to the directional form (§1.4). `skip` is reserved for
delisted coins and ~zero funding only.

## 1.4 Directional form — model the price risk and GATE it (the real risk rule)

The directional short-perp (and long-perp) carries FULL spot-level (directional)
risk on top of the funding carry. It is NOT delta-neutral, so it gets its OWN risk
unit (a directional hard stop, not the basis stop) and its OWN entry hurdle. This
is what turns a "blank check short" into a gated trade.

```python
# ── Directional risk model (§ Resolve A4) ────────────────────────────────
DIRECTIONAL_STOP_BPS   = 200.0   # naked-short/-long hard stop distance (2%)  [tunable]
DIRECTIONAL_LAMBDA     = 0.5     # funding must exceed λ × realized vol        [tunable]
VOL_LOOKBACK_DAYS      = 30      # realized-vol window (markPx closes)          [tunable]
DIRECTIONAL_MIN_HOLD   = MIN_HOLD_HOURS  # reuse 168h cost amortization

def realized_annualized_vol(mark_px_closes: pd.Series) -> float:
    """σ_ann = std(log-returns over VOL_LOOKBACK_DAYS) * sqrt(8760).  0.0 if <2 obs."""

def directional_hurdle_apr(ann_vol: float) -> float:
    """funding hurdle for a directional entry = max(FUNDING_SUSTAIN_FLOOR_APR,
    DIRECTIONAL_LAMBDA * ann_vol).  The funding must more than compensate the
    expected directional volatility cost — a REAL risk rule, not a blank check."""

def directional_risk_gate(mean_apr: float, ann_vol: float) -> dict:
    """Returns {eligible: bool, hurdle_apr: float, reason: str}.
    eligible = mean_apr >= directional_hurdle_apr(ann_vol)  (plus S2/S3 from the
    funding signal checked separately)."""
```

Directional sizing (see §3.3): `notional = (1% capital) / (DIRECTIONAL_STOP_BPS/1e4)`,
so the hard stop = exactly 1R = 1% of capital. Example: $1M capital, 2% stop →
notional $500k (0.5×). The directional hard stop is a MANDATORY exit (market),
independent of funding — if price runs through DIRECTIONAL_STOP_BPS against the
leg, close regardless of funding.

Directional entry (ALL must hold):
    D1  funding_window_signal().sustained                                   (S1-S4)
    D2  directional_risk_gate(): mean_apr >= max(8%/yr, 0.5 × σ_ann)         (hurdle)
    D3  a realizable directional stop (stop distance <= DIRECTIONAL_STOP_BPS,
        notional <= OI capacity rail) — else skip (cannot risk-manage the leg).

FLAG + RESOLUTION (hurdle magnitude): DIRECTIONAL_LAMBDA = 0.5 is a DEFAULT, not a
derived optimum. It encodes "funding must cover at least half the coin's annualized
vol to justify naked directional exposure." It MUST be sensitivity-tested in the
backtest over λ ∈ {0.25, 0.5, 1.0} and the realized directional-loss-vs-funding
ratio reported, so the default is justified by data (mirrors US-180 §2.5's
empirically-justified-default requirement). Do not ship λ = 0.5 unvalidated.

---

# PART 2 — FUNDING vs BASIS DECOMPOSITION

## 2.1 The funding component (creditable, tradeable everywhere)

    funding_pnl = Σ_hours_held  sign * funding_rate(h) * notional
        sign = +1 short perp (receive) / -1 long perp (receive)

Sourced from `fundingHistory.fundingRate` (deep, append-able, verified clean). This
is the structural flow (HL interest floor ~10.95%/yr + premium index paid to the
minority side) and is NOT a mean-reversion artifact. This is the HEADLINE edge.

## 2.2 The basis component (re-source from MARK-ORACLE, not premium)

The honest basis is the perp mark vs spot oracle:

    mark_oracle_basis_bps = (markPx - oraclePx) / oraclePx * 1e4     # signed

Sourced from `assetCtxs` `markPx` / `oraclePx` (§0 P1). The fundingHistory
`premium` is an IMPACT-PRICE premium that feeds the funding calc — it is a DIFFERENT
quantity and is compressed/smoothed; it is NOT a faithful basis and MUST NOT be
credited as basis P&L.

Decomposition rule (binding):
- `funding_pnl` is computed as in §2.1.
- `basis_pnl` is computed ONLY from the real mark-oracle series (§2.3). If a
  historical mark-oracle series is unavailable for a coin, `basis_pnl` is reported
  as `None`/`NaN` and FLAGGED `basis_source="proxy"` (not silently dropped, not
  silently credited).
- The HEADLINE net edge and every G3 metric use `funding_pnl - execution_cost`
  ONLY (funding-only edge). Basis is reported as a SEPARATE, flagged column so a
  proxy basis can never inflate the headline number again.

## 2.3 New mark/oracle snapshot store (the only honest historical basis source)

HL exposes NO history endpoint for markPx/oraclePx. The real basis can only be
accumulated GOING FORWARD by snapshotting `metaAndAssetCtxs` periodically. This is
a NEW store (mirrors hl_funding_store idioms):

New module `scripts/data/hl_assetctx_store.py` (stdlib sqlite3 + pathlib; pandas read):

```python
STORE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_assetctx"
DB_NAME   = "assetctx.db"
_SNAPSHOT_INTERVAL_HOURS = 1          # snapshot cadence (hourly)              [tunable]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS asset_ctx (
    coin          TEXT    NOT NULL,
    time          INTEGER NOT NULL,   -- snapshot time, ms epoch
    mark_px       REAL,               -- assetCtxs markPx
    oracle_px     REAL,               -- assetCtxs oraclePx
    funding       REAL,               -- assetCtxs funding (current hourly)
    premium       REAL,               -- assetCtxs premium (impact-price; kept for provenance)
    open_interest REAL,               -- base coin units
    PRIMARY KEY (coin, time)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_assetctx_coin_time ON asset_ctx (coin, time);
"""

def open_store() -> sqlite3.Connection        # open+create, WAL, idempotent DDL
def append_snapshot(conn, rows: list[dict]) -> int   # INSERT OR IGNORE (coin,time); atomic
def read_basis(coin: str, start_ts=None, end_ts=None) -> pd.DataFrame
    # DataFrame[time, mark_px, oracle_px, basis_bps] where
    # basis_bps = (mark_px - oracle_px)/oracle_px * 1e4.
```

New ingestion `scripts/data/ingest_hl_assetctx.py`:
```python
def fetch_assetctxs() -> tuple[list[dict], list[dict]]
    # POST metaAndAssetCtxs; returns (universe_cfg, asset_ctxs) with isDelisted intact.
def parse_snapshot(meta, ctxs) -> list[dict]
    # rows = [{coin, time(now), mark_px, oracle_px, funding, premium, open_interest}]
    # for every non-delisted coin; mark/oracle parsed with float(ctx.get('markPx'))
    # (correct field names — do NOT copy fetch_hyperliquid_metrics' D2 bug).
def ingest_all(dry_run=False) -> dict     # append_snapshot, atomic, state after success
def main() -> int                          # argparse --dry-run; exit non-zero on hard fail
```

Cron shape: `no_agent`, `resolve_python.sh` interpreter (NEVER bare `python3`),
hourly (`0 * * * *`), `deliver: local`. Polling `metaAndAssetCtxs` once/hour returns
all 235 coins in ONE call (no per-coin pagination) — trivial.

FLAG + RESOLUTION (no historical basis for re-validation): the prior backtest's
`basis_pnl` (54% of net) was `premium`-sourced and is NON-CREDITABLE. The re-validated
strategy's basis component can only be honestly measured after this snapshot store
accumulates history (≈ weeks). Until then the headline edge is funding-only by
construction (§2.2), which is correct and does not depend on the basis term.

## 2.4 Per-episode record schema change (explicit decomposition)

`simulate_carry` output gains columns; every row carries the decomposition and the
basis-source flag:

    coin, entry_ts, exit_ts, exit_reason, execution_form,
    funding_pnl, basis_pnl, basis_source ∈ {'mark_oracle','proxy','none'},
    execution_cost, net_funding (funding_pnl - cost), net_carry,
    notional, risk_usd, net_r, regime_label

where `net_r` (headline) = `net_funding / risk_usd` (funding-only), and `basis_pnl`
is additive but NOT included in `net_r`. `risk_usd` is the corrected 1R (§3).

---

# PART 3 — SIZING FIX (1R = 1% of capital; the 10× misstatement)

## 3.1 The bug (precise)

US-179 `size_position` computes:
    notional = min( (1%*capital)/(kill_basis_bps/1e4), 20%*capital, OI_cap )
For $1M capital and a 50 bps basis stop, the risk-budget rail allows $2M notional,
but `GROSS_NOTIONAL_CAP=0.20` clips it to $200k. Then `basis_risk_usd = $200k *
50bps = $1,000 = 0.1% of capital`. The spec LABELS this "1R" but scores P&L against
a $1,000 unit while implying $10k. Mean episode $641 was reported "+0.64R" when it
was really +$641 on a $1,000 unit = 0.064% of capital — a ~10× misstatement.

## 3.2 Correct sizing math (binding)

1R is DEFINED as 1% of capital at risk (the per-idea budget), and the notional is
the DEPENDENT variable — never the reverse:

    1R                  = CAPITAL_RISK_BUDGET * capital        # = 0.01 * capital
    stop_distance_frac  = stop_bps / 1e4                        # risk distance on notional
    notional            = 1R / stop_distance_frac               # so stop_hit_loss == 1R EXACTLY

    delta-neutral: stop_bps = KILL_BASIS_BPS (50)   -> notional = 0.01*cap / 0.005 = 2× capital
    directional:   stop_bps = DIRECTIONAL_STOP_BPS (200) -> notional = 0.01*cap / 0.02 = 0.5× capital

Then `risk_usd = notional * stop_distance_frac` is ALWAYS == 1% of capital; the "R"
label is honest by construction.

## 3.3 The notional caps must not silently re-shrink the risk unit

The OI-capacity rail (`OI_CAPACITY_FRAC=0.02` of coin OI) is a GENUINE capacity
constraint (you cannot short-funding > 2% of OI without crashing funding toward
zero) and is KEPT. The gross-notional rail is the culprit and is changed:

- DELTA-NEUTRAL branch: `GROSS_NOTIONAL_CAP` is RAISED to permit the risk-budget to
  bind (default 2.0, i.e. ≤ 200% capital), because a true delta-neutral carries
  basis risk, not directional risk, and 2× capital notional with a 50 bps stop is
  the mathematically-correct notional for a 1% basis-risk budget. FLAG: 200%
  notional is real leverage; the user must sign off on the delta-neutral notional
  cap (see F2) — this is a risk-appetite decision, not a derivation.
- DIRECTIONAL branch: no gross-notional rail needed — the directional hard stop
  already binds notional to 0.5× capital for the default 2% stop.

CRITICAL INVARIANT (never misstate R again): if ANY rail (OI capacity, or a
user-chosen notional cap) makes `notional < 1R/stop_distance_frac`, then the
reported `risk_usd` MUST be re-derived from the ACTUAL notional
(`risk_usd = notional * stop_distance_frac`), and `size_capped` MUST be set with the
binding reason — the risk unit is NEVER silently shrunk while a P&L keeps the "R"
label. Every promotion record states `risk_usd` in dollars so the mapping is auditable.

## 3.4 Function-level diff

```python
# funding_carry.py — replace size_position
def size_position(capital: float, stop_bps: float, open_interest_usd: float,
                  execution_form: str, eligible: bool) -> dict:
    """Returns {notional, risk_usd, size_capped, cap_reason, stop_bps}.
    notional = min( (CAPITAL_RISK_BUDGET*capital)/(stop_bps/1e4),   # risk-budget rail
                    gross_cap(capital, execution_form),             # §3.3
                    OI_CAPACITY_FRAC*open_interest_usd )
    risk_usd = notional * stop_bps/1e4                # re-derived from ACTUAL notional
    NOT silently the budget: if capped, risk_usd reflects it and size_capped=True.
    stop_bps = KILL_BASIS_BPS for delta_neutral, DIRECTIONAL_STOP_BPS for directional.
    eligible=False -> {notional:0, risk_usd:0, size_capped:True, cap_reason:'ineligible'}."""

def gross_cap(capital: float, execution_form: str) -> float:
    """delta_neutral/directional_* -> GROSS_NOTIONAL_CAP * capital (default 2.0).
    (directionals are already bound by their stop; this is a backstop.)"""
```

`GROSS_NOTIONAL_CAP` changes 0.20 -> 2.0 (FLAG F2, sign-off).

---

# PART 4 — KILL-STOP FIX (basis_widen on the real mark-oracle basis)

The `basis_widen(perp_mark, spot_oracle)` helper is ALREADY correct — it computes
`(mark - oracle)/oracle * 1e4`. The defect is the CALL SITE: `simulate_carry`
feeds it the `premium` column (compressed impact-price premium), which is why it
fired 2/313 times.

Fix (call-site corrected):
- LIVE path: read `assetCtxs.markPx` / `assetCtxs.oraclePx` (or the §2.3 snapshot)
  and call `basis_widen(markPx, oraclePx)`.
- BACKTEST path: feed `basis_bps` from `hl_assetctx_store.read_basis()` (§2.3)
  as the basis series. When that series is unavailable (coins with no accumulated
  mark/oracle history yet), the basis-widen check is DISABLED for that coin with an
  explicit `basis_source="proxy"` / `stop_unavailable=True` flag — do NOT fall back
  to premium (that re-introduces the inert stop). The `rate_flip` and (directional
  branch) hard-stop exits remain active regardless.

```python
def simulate_carry(funding, basis_real=None, spot=None, params=None) -> pd.DataFrame:
    """basis_real: DataFrame[time, basis_bps] from read_basis() (REAL mark-oracle).
    spot: parsed spot snapshot for execution-form dispatch (§1.2).
    When basis_real is None -> basis_pnl=None, basis_source='proxy', and the
    basis_widen kill is DISABLED (rate_flip + directional stop still active).
    Exit reasons now include 'basis_widen' (real), 'rate_flip', 'decay',
    'directional_stop'."""
```

Exit precedence (unambiguous): directional hard stop first (only directional form),
then rate_flip, then real basis_widen, then decay.

`carry_g3_record` is updated to score `net_funding` (funding-only) against the
corrected `risk_usd`, and to REPORT `basis_pnl` with its source flag rather than
folding it into the headline R.

---

# PART 5 — Cross-cutting: resolved ambiguities, flags, ordering

## 5.1 Ambiguities RESOLVED (with the default)

  A1 "which coins have HL spot today" -> LIVE probe P2: NONE of the CRYPTO_UNIVERSE
     majors have liquid HL spot; only HYPE-ecosystem names (WOW/NEKO/QQQ/GLD/QUANT/
     PURR/BUDDY …) do, and even HYPE itself is spot-illiquid. Resolved by a LIVE
     spot-resolver (§1.2) + liquidity gate, NOT a static list.
  A2 "do not reject non-spot coins" -> dispatch to directional form (§1.3), which is
     the majority (long-perp for funding<0, short-perp for funding>0 where no spot).
  A3 1R unit -> 1R = 1% of capital; notional derived; risk_usd always re-derived from
     actual notional; never silently shrink the labelled risk unit (§3).
  A4 "directional-risk gate threshold" -> DIRECTIONAL_LAMBDA=0.5 × realized vol,
     DIRECTIONAL_STOP_BPS=200, both flagged tunable + sensitivity-validated (§1.4).
  A5 "basis source" -> mark/oracle from assetCtxs; premium is non-creditable; headline
     edge funding-only until snapshot history accumulates (§2).

## 5.2 Flags (need a decision / sign-off)

  F1 fetch_hyperliquid_metrics.py field-name bug (oraclePrice/markPrice/prevDayFunding
     vs oraclePx/markPx/prevDayPx) — pre-existing, OUT of scope; fix in a path-scoped
     follow-up (it silently zeroes OI-USD on that live path today).
  F2 GROSS_NOTIONAL_CAP 0.20 -> 2.0 lets delta-neutral notional reach 2× capital to
     make the 1% basis-risk budget bind. This is a risk-appetite call; requires
     USER SIGN-OFF (leveraged delta-neutral). Alternative if declined: keep the cap
     and REPORT the true (smaller) risk_usd + size_capped (invariant §3.3 still holds).
  F3 No historical mark/oracle series exists; the re-validated basis component can
     only be measured after the §2.3 store accumulates weeks of snapshots.
  F4 DIRECTIONAL_LAMBDA / DIRECTIONAL_STOP_BPS defaults are placeholders pending the
     sensitivity backtest (§1.4); do not treat as final.
  F5 Spot leg for delta-neutral is short-able only long-spot on HL (no spot shorting
     for majors) -> negative-funding delta-neutral is impossible; accepted asymmetry.

## 5.3 Implementation order (each a path-scoped green commit, py_compile clean)

  1. hl_assetctx_store.py (+ unit test: append same (coin,time) twice -> 2nd inserts 0;
     read_basis golden vector).
  2. ingest_hl_assetctx.py + wrapper + hourly cron (no_agent, resolve_python.sh).
  3. funding_carry.py: real-basis helpers (mark_oracle_basis, realized_annualized_vol,
     directional_hurdle_apr, directional_risk_gate), resolve_spot_leg,
     dispatch_execution_form (unit-test thresholds).
  4. funding_carry.py: size_position fix + gross_cap + the §3.3 invariant (unit-test
     that risk_usd == 1% capital when uncapped, and == notional*stop when capped).
  5. funding_carry.py: simulate_carry dispatch + decomposition + real-basis
     basis_widen call-site + directional_stop exit; carry_g3_record funding-only R.
  6. Re-validate on the FULL 235-coin universe (funding-only headline), report the
     directional loss-vs-funding ratio and λ sensitivity table; feed g3_gate.

No edits to trades.csv / journal / publisher / universe.py / live capture / US-180
files in any commit.

END OF DESIGN.