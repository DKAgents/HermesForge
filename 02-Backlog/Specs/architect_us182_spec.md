# Architect Spec — US-182 (Cost-aware Cross-sectional Momentum, Crypto)

Date: 2026-11-02
Author: Architect (HermesForge)
Status: DESIGN ONLY — no pipeline code, no posts, no cron, no .env touched. Awaiting sign-off.
Epic: EPIC-016 (Refactor the Alpha Pipeline)
Scope: cross-sectional momentum signal, transaction-cost-aware construction
(partial rebalance + no-trade band + turnover penalty), BTC 200-DMA regime overlay,
inverse-vol risk constitution, and a backtest on the DEEP HL/OKX bar history that
produces a concrete net-edge verdict through the mandatory G3 fill-realism gate.
Concrete enough for a coder to implement without re-deriving. Every assumption
needing a principal decision is an explicit FLAG, never a silent default.

Summary of the thesis (deleg_337046f4, authoritative): cross-sectional momentum in
crypto grosses ~0.64%/mo but a naive full-turnover construction pays ~63 bps/mo to
trade it — net-negative, the exact "edge smaller than friction" failure that killed
16 of our chart-pattern strategies. Transaction-cost-aware construction (partial
rebalancing TOWARD target weights, not full turnover) raises net Sharpe up to ~2.5x.
In crypto the effect is LOW-BETA DIRECTIONAL (a Bitcoin-regime overlay), not
market-neutral, so the strategy must be built accepting directional beta with a
regime overlay rather than pretending to hedge it away.

DRIVING CONSTRAINT (why now): unlike US-181 (gated on ATM-IV accumulation) and
US-177's 5m retention cliff, DAILY candles are retained DEEP by Hyperliquid
(980+ bars/coin, and the OKX proxy fills the pre-store gap for 32/35 tickers).
The full input — daily closes for the momentum rank, the BTC 200-DMA, and the
inverse-vol weights — is already on disk. This design produces a NET-EDGE VERDICT
on existing data, NOT a paper-forward deferral.

---

## 0. Ground truth read (verified — do not re-derive)

Files read in full:
- 02-Backlog/Stories/US-182-CostAware-Momentum.md
- scripts/data/hl_bar_store.py          (load_bars union read: HL store + labeled OKX proxy)
- scripts/data/okx_proxy.py             (HL->OKX symbol map; 32/35 mapped, kBONK/kPEPE/kSHIB/PAXG unmapped)
- scripts/gauntlet/fee_source.py        (get_round_trip_bps("crypto") = taker 4.5*2 + slip 2.5 + funding 0.5 = 12.0 bps)
- scripts/gauntlet/cost_adjuster.py     (compute_cost_drag; the G3 bar-level cost model)
- scripts/gauntlet/g3_gate.py           (mandatory fill-realism gate; daily crypto -> BAR-LEVEL model)
- scripts/gauntlet/funding_carry.py     (the carry_g3_record pattern to mirror; CAPITAL_RISK_BUDGET=0.01, GROSS_NOTIONAL_CAP=1.0)
- scripts/hermes_config/universe.py     (CRYPTO_UNIVERSE, 35 tickers, single source of truth)
- trading/proposals/PROP-001-hermes-strategy-gauntlet.md (G0 cost-first, G3/G4/G5/G6, DSR/PBO, BTC-beta clustering)

CONFIRMED FACTS (binding):
1. COST (single fee table, fee_source.py): crypto all-in round trip =
   taker 4.5*2 + slippage 2.5 + funding 0.5 = 12.0 bps (get_round_trip_bps("crypto")).
   This is the 12 bps the story references. Cost must come from here, never re-listed.
2. G3 ROUTING: g3_gate routes intraday crypto (5m/1h/6h) to the L2 execution_sim;
   EVERYTHING ELSE — including DAILY-bar crypto — goes through the BAR-LEVEL
   hostile model (next-open entry + compute_cost_drag + worst-print exit). A
   daily-rebalance cross-sectional strategy is timeframe "1d" -> bar-level path.
3. The 1d bars are deep (980+/coin) and the OKX proxy fills the pre-store gap for
   32/35 tickers (kBONK/kPEPE/kSHIB = 1000x base-denom, no OKX twin; PAXG = no OKX
   perp). So a DAILY-bar backtest is data-complete NOW. This is the ONE refactor
   direction backtestable immediately, exactly as the story says.
4. PRECEDENT for a strategy whose cost model is INTERNAL: funding_carry.carry_g3_record
   repMigrates the G3 gate SEMANTICS (MIN_TRADES=10, realistic mean R > 0,
   pessimistic PF > 1.0, realistic >= 0.60*optimistic) with the strategy's own cost
   model, rather than feeding assert_g3_gate's compute_cost_drag (which would
   double-count). US-182 follows the same pattern (see §5.3, F10).

Import direction (one-way, acyclic — mirrors funding_carry.py):
  xsmom.py -> hl_bar_store.py + fee_source.py + hermes_config.universe
              + g3_gate (MIN_TRADES / EDGE_DECAY_FLOOR constants only)

---

# PART 1 — SIGNAL (cross-sectional momentum rank)

## 1.1 Momentum score (per name, daily closes)

    momentum_i(t) = close_i[t - SKIP] / close_i[t - LOOKBACK] - 1

LOOKBACK (primary) = 30 days; SKIP = 1 day. The SKIP drops the most-recent daily
bar to dodge the well-documented short-term (1-day) reversal; the lookback is
measured back FROM the skipped bar, so the score is (P[t-1]/P[t-30] - 1).

    MOMENTUM_LOOKBACK_DAYS = 30    [tunable; 7 and 90 are the sensitivity legs]
    MOMENTUM_SKIP_DAYS     = 1     [tunable; skip>0 is the reversal-dodge, keep >=1]

FLAG F2: lookback 30d (≈1 month) is primary per the 0.64%/mo research figure; 7d
and 90d are sensitivity legs to prove the effect is not a single-frequency
artifact. Skip = 1 day is the standard, but the PRINCIPAL may prefer skip = 1
week (skip the most-recent rebalance period). Default 30d / skip 1d.

## 1.2 Cross-section: rank and leg membership

At each rebalance timestamp t, rank all universe names by momentum_i(t)
descending. Long = top quintile (top 20%); short = bottom quintile (bottom 20%).

    TOP_FRAC    = 0.20    (long leg = top 20% by momentum)      [F4: quintile vs decile]
    BOTTOM_FRAC = 0.20    (short leg = bottom 20% by momentum)

FLAG F1 (direction): PRIMARY = long-short (long top quintile, short bottom
quintile). Hyperliquid perps allow shorting with no borrow, so the short leg is
fully available. ALTERNATIVE = long-flat (long top quintile only, no short leg),
which is simpler and sidesteps short-leg funding entirely but halves the spread
exposure. Default long-short; the regime overlay (§3) already drops the short leg
when BTC is below its 200-DMA, so the "down-regime" state IS the long-flat form.
FLAG F4: quintile (20%) cut is the default; deciles (10%) are the sensitivity leg.
A finer cut concentrates the spread but raises turnover churn across the cut.

## 1.3 Universe (backtestable set)

Source: hermes_config.universe.CRYPTO_UNIVERSE (35). For a DAILY backtest the
kilocoins (kBONK/kPEPE/kSHIB) trade on a ~1000x off-scale base and have no OKX
proxy twin (short/mixed history), and PAXG is a gold-pegged near-zero-vol asset
that would blow up inverse-vol weights. Default backtest universe = CRYPTO_UNIVERSE
minus {kBONK, kPEPE, kSHIB, PAXG} = 31 names, further filtered by a liquidity
floor (PROP-001 G1-inspired):

    MIN_DAILY_NOTIONAL_USD = 250_000.0   # median 30d daily base-volume * price
    MIN_VOL_GATE           = 0.20        # 30d realized vol >= 20% ann (drop dead coins)

FLAG F7: the exact liquidity floor and the kilocoin/PAXG exclusion are a principal
decision. The floors above are defaults; tighten/loosen, but a name with no
tradeable daily liquidity or near-zero vol must never enter a momentum leg.

# PART 2 — COST-AWARE CONSTRUCTION (partial rebalance + band + turnover penalty)

The heart of US-182. The target-portfolio is computed fresh each rebalance, but the
ACTUAL portfolio only moves partway toward it, and only where the drift clears the
taker cost. This is the standard solution to the turnover-penalized objective:

    minimize  -E[ Σ_i w_i r_i ]  +  λ * ( Σ_i |Δw_i| ) * round_trip_bps

which the closed-form rule below approximates with two knobs (κ partial speed, η band).

## 2.1 Target weights (what we WANT to hold)

Within each leg, weights are inverse-vol (risk parity), normalized to the leg's
gross: σ_i = 30-day realized annualized vol of DAILY close log-returns (√365).

    σ_i(t)        = std(log-returns of close_i over VOL_LOOKBACK_DAYS=30 daily bars) * sqrt(365)
    raw w*_i      = 1 / σ_i                      (within leg only)
    w*_i (long)   = raw_i / Σ_j raw_j * LONG_GROSS       (LONG_GROSS  = 0.5)
    w*_i (short)  = -(raw_i / Σ_j raw_j * SHORT_GROSS)   (SHORT_GROSS = 0.5)

    VOL_LOOKBACK_DAYS = 30      [F12: daily closes / √365; 5m bars an alternative]

FLAG F12: inverse-vol is computed on DAILY closes (√365 annualization) for
consistency with the daily momentum signal. The alternative (5m bars, √105120) is
a refinement, not required for v1.

## 2.2 Rebalance rule (the exact mechanism — implement this verbatim)

On each rebalance date T, given current weights w (from the prior date) and target
weights w* (§2.1, after overlay §3 has zeroed/scaled legs):

    For each name i with |w*_i| > 0 or |w_i| > 0:
        MEMBERSHIP CHANGE  (w_i==0 XOR w*_i==0, i.e. the name enters or leaves a leg):
            Δw_i = w*_i - w_i                     # trade FULL weight immediately
        IN-LEG DRIFT      (both w_i and w*_i non-zero, same sign):
            d_i = w*_i - w_i
            if |d_i| <= band_i:  Δw_i = 0.0       # NO-TRADE BAND: drift doesn't pay cost
            else:                 Δw_i = KAPPA * d_i   # PARTIAL move toward target

    band_i = BAND_FRAC * |w*_i|                    # drift band as a fraction of target

    KAPPA     = 0.5    # partial-rebalance speed (fraction of drift to close) [F5]
    BAND_FRAC = 0.25   # no-trade band width, as a fraction of target weight  [F5]

    turnover = Σ_i |Δw_i|                          # one-way turnover (weight fraction)
    cost_t   = get_round_trip_bps("crypto") / 1e4 * turnover * capital

Cost convention (F9): charge the FULL crypto round-trip (12 bps) per dollar of
one-way turnover. Over the life of the book each dollar is bought once and sold
once, so total cost = Σ turnover_t * 12 bps is the correct lifetime cost and is
fail-closed. Do NOT charge a separate per-side taker on top.

WHY MEMBERSHIP CHANGES TRADE FULL WEIGHT: a name crossing the quintile cut is a
position OPEN/CLOSE (target goes 0 <-> w*), not a re-weight. Deferring it via KAPPA
would leave a stale sized position during the moment it is most important (rank
flip). Only IN-LEG drift (a name already held, target weight drifting) gets the
band + partial smoothing. This is the single most important implementation detail;
getting it wrong silently re-introduces the naive full-turnover cost.

## 2.3 What the knobs buy (verify in the backtest)

    KAPPA < 1  -> reduces turnover by moving partway; a name re-entering the top
                 quintile after a brief dip re-builds weight gradually.
    band_i > 0 -> kills tiny noise trades whose drift is smaller than the 12 bps
                 they would pay to make. band_i == BAND_FRAC * |w*_i| scales the
                 band with position size so it clears the cost in marginal terms.
Default run sweeps KAPPA in {0.25, 0.5, 0.75, 1.0} and BAND_FRAC in {0.0, 0.25,
0.5} to show the Sharpe-vs-turnover curve; KAPPA=0.5 / BAND_FRAC=0.25 is the
shipping default. KAPPA=1.0 / BAND_FRAC=0.0 reproduces the NAIVE full-turnover
baseline that is expected to be net-negative — this is the A/B the whole story is
about, and it MUST be reported side by side.

# PART 3 — REGIME OVERLAY (BTC 200-DMA)

The strategy is a BETA overlay, not market-neutral: the crypto cross-section
co-moves with BTC, so a gross-neutral long/short spread still carries residual BTC
beta. We accept that beta and gate it with a trend overlay rather than hedging it.

## 3.1 Overlay rule (exact)

    btc_200dma(t) = mean(BTC daily close over trailing 200 bars, at t)
    OVERLAY_UP(t) = close_BTC(t) > btc_200dma(t)

    if OVERLAY_UP:   run the FULL construction (long top + short bottom),
                     gross = LONG_GROSS + SHORT_GROSS = 1.0
    if NOT (down):   SHORT leg = 0 (drop it entirely), long leg scaled by
                     DOWN_SCALE = 0.5, so gross = 0.5 long-only.

    DOWN_SCALE = 0.5    [F6]

FLAG F6: the overlay is BTC 200-DMA binary, with the short leg dropped and the
long leg halved in the down-regime. Alternatives for the principal: (a) a 2-DMA
filter (50 > 200), (b) scale exposure DOWN_SCALE instead of the all-or-nothing
drop, (c) use BTC 30-day return (> +2% / < -2%) as funding_carry's
partition_regime already does. Default = 200-DMA binary + short-drop + 0.5 long.

The 200-DMA is computable NOW: BTC daily bars are deep (980+ via HL 1d + OKX proxy).

# PART 4 — RISK CONSTITUTION (inverse-vol + gross cap + 1R invariant)

## 4.1 The rails (binding)

    GROSS_EXPOSURE_CAP = 1.0     # Σ_i |w_i| <= 1.0 — NO leverage, ever (F11)
    LONG_GROSS  = 0.5            # long leg gross when overlay up
    SHORT_GROSS = 0.5            # short leg gross when overlay up
    MAX_NAME_WEIGHT = 0.10       # no single name > 10% gross (diversification floor)
    CAPITAL_RISK_BUDGET = 0.01   # 1R = 1% of capital (reuse funding_carry constant)
    MARGIN_CAP_FRAC = 1.0        # margin deployed <= 1x capital (no leverage; F11)

The 1R = 1% capital invariant is IDENTICAL to funding_carry (§3.3) and US-181 (§4.2):
notional is the DEPENDENT variable; risk_usd is the labelled unit; a capped
position re-derives risk_usd from actual notional and is flagged, never silently
shrunk. For a portfolio, risk_usd per period = CAPITAL_RISK_BUDGET * capital, and
every promotion record states risk_usd in dollars.

MARGIN_CAP_FRAC = 1.0 and GROSS_EXPOSURE_CAP = 1.0 are both held UNTIL G3-proof
(F11). No leverage is enabled in this design, period; a 2x levered form is a
separately-signed later risk, exactly as US-181 F7b and funding_carry F2 gate it.

## 4.2 Sizing (function surface — mirror funding_carry.size_position)

    def size_book(capital, weights, gross_cap=GROSS_EXPOSURE_CAP,
                  margin_cap_frac=MARGIN_CAP_FRAC, vol_series=None) -> dict:
        # weights: signed target weights (long +, short -), already overlay-gated
        # returns {weights, notional_per_name, gross_notional, net_notional,
        #          margin_deployed, size_capped, cap_reason, risk_usd}

    CRITICAL INVARIANT: if any rail (gross cap, name cap, margin cap) scales a
    weight down, the reduction is recorded as size_capped with the binding reason,
    and risk_usd is re-derived from ACTUAL gross notional. The "R" label is never
    silently shrunk while a P&L keeps the label.

# PART 5 — BACKTEST + G3 (concrete net-edge verdict on existing data)

## 5.1 Data assembly (pure read — no ingest, no promotion)

    1. For each name in the backtest universe (F7): load_bars(name, "1d",
       warmup_start, now) from hl_bar_store (union of HL 1d + OKX proxy pre-store
       gap). The returned 'source' column (hyperliquid/okx_proxy) MUST be surfaced
       in the panel metadata — never silently mixed (US-177 policy).
    2. Pivot to a price panel P[date x name] on the common daily timestamps (ms->UTC
       day). Outer-join all names; forward-fill close gaps <= 2 days; drop a name
       if its history < (ADS + 200) days where ADS = signal warmup (200 bars for the
       BTC DMA is the binding floor). FLAG F13 for the exact floor.
    3. BTC close series for the 200-DMA from the same panel.

FLAG F13: mixing HL 1d with the OKX proxy for the pre-store gap is the honest
"source differs per name" reality (US-177). DROP any name whose backtest window is
predominantly proxy (survivorship-bias guard, PROP-001 §06). Default: require the
window be >= 90% same-venue (source='hyperliquid') or drop the name.

## 5.2 Simulation walk (daily, weekly rebalance)

    REBALANCE_PERIOD = 7 days   # weekly; daily is the high-turnover sensitivity leg [F3]

    For each day t ascending:
        r_i,t = close_i(t)/close_i(t-1) - 1               # daily returns
        if t is a rebalance date (every 7 days):
            compute momentum_i(t) (§1.1), rank, legs (§1.2)
            compute w* (§2.1), apply overlay (§3), apply band+partial (§2.2)
            charge cost_t = 12 bps * turnover * capital   (§2.2)
            w <- w + Δw
        portfolio return that day = Σ_i w_i * r_i,t  -  (cost_t if rebalance else 0)

    Output a daily NAV series + one "episode" per rebalance holding period.

FLAG F3: REBALANCE_PERIOD = weekly is primary (matches the 30d lookback and keeps
turnover tractable). DAILY is the sensitivity leg that exercises the partial
rebalance hardest (that is where κ<1 earns its keep). Both must be run; weekly is
the shipping default.

## 5.3 Net-edge + G3 record (mirror carry_g3_record, NOT literal assert_g3_gate)

Unit of observation = one rebalance holding period. Its R is the period's net
portfolio return divided by risk_usd (= 1% capital). Because the strategy's cost
is ALREADY netted internally (turnover * 12 bps), the correct G3 evaluation is a
module-local record that applies the GATE SEMANTICS with the strategy's own cost
model — exactly the funding_carry.carry_g3_record precedent (and US-181 F13's cost
double-counting warning). Feeding assert_g3_gate's compute_cost_drag would
DOUBLE-COUNT the 12 bps. FLAG F10.

    def xsmom_g3_record(episodes) -> dict:
        optimistic_r  = gross period return / risk_usd      (zero cost; diagnostic)
        realistic_r   = (gross period return - turnover*12bps) / risk_usd
        pessimistic_r = realistic_r  -  get_taker_bps("crypto")/1e4 * turnover / risk_usd
                         # one extra adverse (worst-fill) taker leg per side, the
                         # G3 stand-in for worst-print / missed trade-through exit

        Apply gate thresholds (import MIN_TRADES, EDGE_DECAY_FLOOR from g3_gate):
          n >= 10, realistic mean R > 0, pessimistic PF > 1.0,
          realistic >= 0.60 * optimistic
        Returns {n, optimistic_mean_r, realistic_mean_r, pessimistic_pf,
                 edge_decay_ratio, passed, reasons, turnover, cost_bps, r_unit}.

The pessimistic leg is the BINDING test: it layers one extra taker leg on the
rebalance turnover (the worst-fill assumption), which is precisely where a
thin-edge cross-sectional strategy lives or dies. turn over is REPORTED alongside
every record so "did partial rebalance actually cut the cost" is inspectable.

## 5.4 Regime + concentration partition (G6, PROP-001)

Same as funding_carry.partition_regime, plus:
    - BTC-beta clustering: assign each name to a cluster by rolling 30d BTC beta
      (correlation_state / correlation_state.py's btc_beta), report P&L per cluster.
    - G6 pass: non-negative in >= 3 of 4 regimes; edge present in >= 2 of 3 beta
      clusters; no single symbol > 35% of P&L; no single month > 40%.
    - Because this is a LOW-BETA DIRECTIONAL strategy, G6's "present in >= 2 of 3
      beta clusters" is the test that the spread edge is NOT just a BTC beta bet
      — it must survive within correlated clusters, not only across them.

## 5.5 Multiple-testing + CPCV (G4/G5, PROP-001)

    - CPCV: N=12 groups, k=2 test groups -> 66 splits, 11 reconstructed paths.
      PURGE the holding horizon (>= 1 rebalance period) and EMBARGO after.
    - G4 pass: median split PF >= 1.3, 10th-pct split PF >= 1.0, worst-path max-DD
      within budget, block-bootstrap p < 0.05.
    - G5 pass: DSR > 0.95, PBO < 0.30, N + values written to the strategy note.
    The KAPPA/BAND_FRAC sweep (§2.3) runs INSIDE the CPCV folds — the shipping
    KAPPA/BAND_FRAC is chosen on TRAIN folds only, else the sweep itself overfits.

## 5.6 Pre-registered kill rules + the verdict

Pre-register (hypothesis-register, G5) BEFORE the backtest, ledger one row:
    HYPOTHESIS: cost-aware (κ=0.5, η=0.25) cross-sectional momentum, 30d/skip-1d,
                weekly, BTC-200DMA overlay, long-short -> net Sharpe > 0 through G3.
    FALSIFIERS (any one => no claimable edge, demote to Hypothesis, per G3 REJECT):
      (a) realistic mean R <= 0 through xsmom_g3_record,
      (b) pessimistic PF <= 1.0,
      (c) realistic < 0.60 * optimistic,
      (d) naive baseline (κ=1.0, η=0.0) net Sharpe NOT below the cost-aware net
          Sharpe (the partial rebalance must DEMONSTRABLY beat full turnover, else
          the entire thesis is false on this data).

The deliverable is a report mirroring reports/backtester/funding_carry_revalidation_us185.md:
side-by-side NAIVE vs COST-AWARE net Sharpe, mean R, PF, turnover, the G3 record
(passed/reason), CPCV split stats, DSR/PBO, and the regime/beta-cluster partition.
A NET-EDGE VERDICT is stated explicitly: G3 pass -> promotable hypothesis (still
paper); G3 fail -> demote to Hypothesis with the citable reason. NO paper-forward
deferral — the daily-bar data is already complete (§0 fact 3).

---

## 6. Cross-cutting: resolved ambiguities, flags, implementation order

### 6.1 Ambiguities RESOLVED (with default)
  A1 Signal -> 30d lookback, skip 1d, top/bottom quintile, long-short (§1).
  A2 Construction -> inverse-vol target + partial rebalance (κ=0.5) + no-trade band
     (η=0.25), membership changes trade full weight, 12 bps per unit turnover (§2).
  A3 Overlay -> BTC 200-DMA binary; down-regime drops short leg, halves long (§3).
  A4 Risk -> inverse-vol, gross cap 1.0, 1R=1% capital, no leverage, margin cap 1.0 (§4).
  A5 Backtest -> daily bars via load_bars(HL+OKX), weekly rebalance, ranks + legs +
     overlay + band/partial, cost on turnover (§5.1–5.2).
  A6 G3 -> xsmom_g3_record mirroring carry_g3_record (internal cost model), NOT
     literal assert_g3_gate (avoid double-count) (§5.3).
  A7 Overfit control -> CPCV(N=12,k=2) + DSR/PBO, KAPPA/BAND chosen on train folds (§5.5).

### 6.2 Flags (need a principal decision / sign-off)
  F1  Long-short vs long-flat. Default long-short (perps allow short); down-regime
      state is already the long-flat form.
  F2  Momentum lookback 30d primary; skip 1d (vs skip 1wk). Sensitivity 7d/90d.
  F3  Rebalance weekly (primary) vs daily (sensitivity). Weekly default.
  F4  Quintile (20%) cut vs decile (10%). Quintile default.
  F5  KAPPA=0.5, BAND_FRAC=0.25 defaults; swept in {0.25..1.0} x {0,0.25,0.5}.
  F6  Overlay = BTC 200-DMA binary + short-drop + 0.5 long. Alternatives: 50/200
      filter, exposure scaling, BTC 30d ret (funding_carry style).
  F7  Backtest universe = 31 names (drop kBONK/kPEPE/kSHIB/PAXG) + liquidity floor
      (median daily notional >= $250k, 30d vol >= 20% ann). Threshold is a decision.
  F8  Short-leg FUNDING accrual is OMITTED in v1 (fee_source's 0.5 bps is the only
      funding charge). A funding-aware extension (hl_funding_store) is future work.
      Flagged so shorts are not silently free of funding drag.
  F9  Cost convention = full 12 bps round-trip per dollar of one-way turnover
      (fail-closed, lifetime-correct). Do not re-add a per-side taker on top.
  F10 G3 integration = xsmom_g3_record (internal cost model), NOT literal
      assert_g3_gate. This is the US-185 carry_g3_record / US-181 F13 precedent.
      Sign-off confirms we do NOT double-count.
  F11 No leverage: GROSS_EXPOSURE_CAP=1.0, MARGIN_CAP_FRAC=1.0 held until G3-proof.
      A 2x levered long-short is a separately-signed later risk.
  F12 Inverse-vol on daily closes (√365), 30d lookback. 5m bars (√105120) is a
      refinement, not v1.
  F13 Panel assembly: HL 1d + OKX proxy for pre-store gap; require >= 90% same-venue
      or drop the name (survivorship bias). Exact floor is a decision.
  F14 (design note, resolved) membership change (0<->w*) trades FULL weight, only
      IN-LEG drift gets band+partial — do not partial-surface a cut-cross (§2.2).

### 6.3 Implementation order (each a path-scoped green commit, py_compile clean)
  1. xsmom.py: momentum_score + cross_sectional_rank + realized_vol_daily + unit
     tests (golden vectors: flat series -> 0 momentum; known rank split).
  2. xsmom.py: target_weights (inverse-vol) + btc_200dma_overlay + unit tests
     (weight sum == leg gross; overlay flip at the 200-DMA crossing).
  3. xsmom.py: rebalance() — band + partial + membership-full-trade — unit tests
     (membership change trades full Δw; in-leg drift under band trades 0; turnover
     == Σ|Δw| consistency).
  4. xsmom.py: simulate_xsmom (daily walk, weekly rebalance, cost on turnover) +
     Size_book (1R invariant) + unit tests (risk_usd == 1% capital when uncapped).
  5. xsmom.py: xsmom_g3_record (mirror carry_g3_record) + partition (regime +
     beta-cluster) + the NAIVE-vs-COST-AWARE side-by-side report.
  6. Backtest run over the deep 1d panel (load_bars); CPCV(N=12,k=2) + DSR/PBO;
     write reports/backtester/xsmom_costaware_revalidation.md with the explicit
     net-edge verdict.

No edits to trades.csv / journal / publisher / universe.py / live capture /
fee_source.py / g3_gate.py. hl_bar_store.py and hermes_config.universe.py are
READ, not written. The strategy writes NO live state; it is read-only research.

END OF DESIGN.