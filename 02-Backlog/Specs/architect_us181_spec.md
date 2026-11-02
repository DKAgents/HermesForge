# Architect Spec — US-181 (Short-Vol / Short-VRP with Vol-of-Vol Timing)

Date: 2026-11-02
Author: Architect (HermesForge)
Status: DESIGN ONLY — no pipeline code, no posts, no cron, no .env touched. Awaiting sign-off.
Epic: EPIC-016 (Refactor the Alpha Pipeline)
Scope: instrument + construction, vol-of-vol timing rule, tail-risk constitution,
margin model, backtest + G3. Concrete enough for a coder to implement without
re-deriving. Every assumption that needs a principal decision is an explicit FLAG,
never a silent default.

Summary of the thesis (deleg_337046f4, authoritative): the negative variance-risk
premium (implied > realized) is the most robustly documented premium, but
UNCONDITIONAL short-vol is tail-risky ("pennies in front of a steamroller") — the
exact failure the funding-carry directional form just hit (hard stop wiped 20–39×
the funding earned; G3 failed at every λ). Conditioning short-vol on vol-of-vol
(morning VVIX-style) yields Sharpe 0.76–3.24, ~2–3× unconditional, and the signal
decays by midday (a genuine under-reaction). The edge is the RISK PREMIUM
(implied > realized), timed to skip the vol-spike steamroller.

---

## 0. Ground truth read (verified — do not re-derive)

Files read in full:
- 02-Backlog/Stories/US-181-Vol-VRP-Timing.md, US-187-Options-IV-Surface.md
- 02-Backlog/Epics/EPIC-016-Refactor-Alpha-Pipeline.md
- scripts/data/iv_store.py            (NOTE: the story prompt said
  scripts/gauntlet/iv_store.py — the module actually lives in scripts/data/ and
  vol_of_vol_gate.py imports it from there. See F14.)
- scripts/data/ingest_deribit_iv.py
- scripts/gauntlet/vol_of_vol_gate.py (STUB — vol_of_vol_level() exists; the gate
  threshold 0.5 is a PLACEHOLDER US-181 must derive, not adopt)
- scripts/gauntlet/g3_gate.py         (mandatory fill-realism promotion gate)
- scripts/gauntlet/fee_source.py      (dynamic HL cost source — HL PERP fees only)
- scripts/gauntlet/funding_carry.py   (the US-185 sizing-fix + G3 pattern to mirror)
- scripts/data/hl_bar_store.py        (5m crypto bars — the realized-vol / payoff source)
- scripts/discord/options_recommender.py (Black-Scholes greeks already present)
- 02-Backlog/Specs/architect_us185_spec.md, architect_us186_188_spec.md (format + reuse)
- reports/backtester/funding_carry_revalidation_us185.md (the steamroller failure)

LIVE STORE PROBE (read-only; no state written):
- dvol_index  BTC: 721 hourly candles, min_ts 1790985600000 → max_ts 1793577600000
  = ~30 days (Deribit bounds the reach). ETH identical.
- crypto_atm_iv BTC: 13 rows, ALL at a single ts 1793577600000 (one snapshot).
  The ATM IV term structure is FORWARD-ONLY — it just began accumulating.
- CONSEQUENCE (binding): the premium side (ATM IV) has essentially no history yet;
  the realized side (5m bars in hl_bar_store) is deeper. The binding constraint on
  any G3-grade backtest is the ATM IV accumulation window (see §5.4).

Import direction (one-way, acyclic) — the new module mirrors funding_carry.py:
  vol_vrp.py -> iv_store.py + hl_bar_store.py + vol_of_vol_gate.py
                + fee_source + g3_gate

---

# PART 1 — INSTRUMENT + CONSTRUCTION

## 1.1 What is sold

Short an ATM straddle on BTC and ETH via Deribit options. One straddle = short 1
ATM call + short 1 ATM put at the same strike K = nearest underlying spot S0, same
expiry. The US-187 store gives us everything needed to price it WITHOUT a live
chain re-fetch at backtest time:

  S0   = crypto_atm_iv.spot            (underlying at snapshot)
  σ0   = crypto_atm_iv.atm_iv          (ATM IV, %, = 0.5*(call+put mark_iv))
  T0   = crypto_atm_iv.dte / 365       (years to expiry)
  K    = nearest strike to S0          (ATM; for the store's purposes K := S0)

The straddle greeks ARE reconstructable: options_recommender.py already carries
_norm_cdf, _norm_pdf, _bs_d1, _bs_delta, _bs_theta, _bs_gamma. Two one-liners must
be ADDED (do not re-derive the rest): _bs_price and _bs_vega (formulas in §1.3).

FLAG F1 (instrument choice): ATM straddle is the PRIMARY. A strangle (OTM wings
sold) is the alternative if the principal wants a wider profit band, but it needs
OTM IV (skew) which the store does NOT have (only ATM IV). A pure variance proxy
(variance swap / delta-hedged short straddle) is NOT available on Deribit retail
and is out of scope. Default = ATM straddle; sign-off required only if strangle is
preferred.

FLAG F3 (universe): BTC + ETH only. Deribit lists SOL options too, but the US-187
store ingests only BTC/ETH (CURRENCIES = ("BTC","ETH")). Adding SOL = a store
extension, out of scope here. Default = BTC + ETH.

## 1.2 The PnL identity (binding — this is the whole edge)

Two forms, both computed from the store + underlying bars. The HELD-TO-EXPIRY form
is the primary (it is the VRP itself); the MARK-TO-MARKET form is used for early
exits (vol-spike stop, §3) and for the midday-decay handling (§2.3).

HELD-TO-EXPIRY (primary — "implied vs realized"):

    premium_collected = C(S0,K,T0,σ0) + P(S0,K,T0,σ0)      # BS, r=0 (§1.3)
    realized_payoff   = |S_T - K|                            # straddle intrinsic at expiry
    gross_pnl         = premium_collected - realized_payoff
    net_pnl           = gross_pnl - execution_cost           # §5.2 cost model

    S_T = underlying close at expiry, from hl_bar_store 5m bars (last bar ≤ expiry).

MARK-TO-MARKET (early exit at t1, spot S1, IV σ1, DTE T1):

    premium_at_exit = C(S1,K,T1,σ1) + P(S1,K,T1,σ1)
    mtm_pnl = premium_collected - premium_at_exit - execution_cost
            = theta_pnl + gamma_pnl + vega_pnl
    theta_pnl  = +θ_straddle * Δt_days        (short straddle EARNS theta)
    gamma_pnl  = -0.5 * Γ_straddle * (ΔS)^2   (short gamma LOSES on realized move)
    vega_pnl   = -ν_straddle * Δσ             (short vega LOSES when IV rises)

    θ_straddle = θ_call + θ_put (per day); Γ_straddle = Γ_call + Γ_put;
    ν_straddle = ν_call + ν_put (per 1 vol point, i.e. per 1% σ).

This maps exactly to the story's "premium collected minus realized-vol path minus
IV move": premium collected = theta_pnl (time decay of the collected premium);
realized-vol path = gamma_pnl; IV move = vega_pnl.

## 1.3 Black-Scholes formulas (add to a shared helper; do not re-derive)

r = 0 (crypto; no meaningful risk-free rate — FLAG F12). σ in decimal (σ0/100).

    d1 = (ln(S/K) + (σ²/2)·T) / (σ·√T)      d2 = d1 - σ·√T
    C  = S·N(d1) - K·N(d2)                   P  = K·N(-d2) - S·N(-d1)
    ν  = S·√T·N'(d1) / 100                   (per 1 vol point = 1% σ)
    Γ  = N'(d1) / (S·σ·√T)
    θ  = -(S·N'(d1)·σ) / (2·√T) / 365        (per day; call ≈ put at ATM)

FLAG F5 (BS on coin-settled options): Deribit BTC/ETH options are coin-settled
("reversed"), so Black-Scholes is an APPROXIMATION for the greeks. mark_iv is
quoted directly (no BS solve needed for IV), but the BS greeks on a coin-settled
option are approximate. For a backtest this is acceptable (the VRP is a first-order
effect, and the held-to-expiry payoff |S_T - K| is exact regardless of settlement).
Flagged so the coder does not silently treat BS greeks as exact.

---

# PART 2 — VOL-OF-VOL TIMING RULE

## 2.1 The predicate (entry)

    enter_short_vol(t) = VOV_CALM(t) AND VRP_RICH(t) AND MORNING(t)

    VOV_CALM(t)  = vol_of_vol_level(currency, window_hours=30*24) < VOV_THRESHOLD
    VRP_RICH(t)  = atm_iv(t) > realized_vol(t) * VRP_MULT
    MORNING(t)   = t is a morning snapshot (see §2.3)

vol_of_vol_level() is the EXISTING stub measurement (realized vol of the DVOL index
close over the trailing 30d, annualized by √8760). It is a LEVEL, not a signal —
US-181 layers the threshold on top. The stub's vol_of_vol_gate(threshold_ann=0.5)
is a PLACEHOLDER and MUST NOT be adopted; the threshold is derived in §2.2.

realized_vol(t) = realized annualized vol of the underlying from hl_bar_store 5m
bars over the trailing 30d (std of log-returns × √(365·24·12) = √105120). This is
the SAME quantity funding_carry.realized_annualized_vol computes, but on 5m bars
rather than hourly markPx (FLAG F11 — bar interval + annualization).

## 2.2 Threshold DERIVATION (not a magic constant)

VOV_THRESHOLD is derived from data, never hardcoded. Procedure (runs once the store
has enough history, §5.4):

  1. For every historical day d, compute vol_of_vol_level(d) (morning snapshot).
  2. For every day d, compute the FORWARD held-to-expiry net_pnl of an
     unconditional short straddle entered at d's morning snapshot (§1.2).
  3. Bucket days by vol_of_vol_level into deciles (or a finer grid).
  4. Report mean net_pnl / Sharpe per bucket. The VRP is positive in the LOW
     vol-of-vol buckets and negative (steamroller) in the HIGH buckets.
  5. VOV_THRESHOLD := the vol-of-vol level at the bucket boundary where forward
     mean net_pnl crosses from positive to negative (the "steamroller boundary").
  6. Cross-validate the threshold with CPCV (N=12, k=2, per PROP-001) and report
     the threshold's stability across folds. If the boundary is not stable, the
     strategy is NOT promotable (the timing edge is not robust).

VRP_MULT default = 1.0 (implied must exceed realized). A conservative 1.1–1.2
(only enter when the premium is RICH) is the sensitivity alternative. FLAG F10.

## 2.3 Midday-decay handling (signals stale after entry day)

The vol-of-vol signal is a MORNING measurement and decays by midday (the market
under-reacts then reprices). Binding rules:

  - MORNING(t): entries are evaluated ONLY on the first DVOL/ATM-IV snapshot of the
    UTC day (or a fixed morning hour). The DVOL store is hourly; "morning" = the
    first hourly candle of the UTC day. FLAG F9 (exact morning hour — default 00:00
    UTC, i.e. the first candle of the day; a later hour e.g. 08:00 UTC is the
    alternative if the principal wants a "market-open" anchor).
  - A vol-of-vol reading from day T authorizes an entry on day T ONLY. It does NOT
    authorize entries on day T+1 — a fresh morning reading is required each day.
  - Once entered, the position is NOT re-sized or re-entered on a stale midday
    signal. The vol-of-vol gate is an ENTRY filter, not a continuous re-entry
    trigger. The only intraday/ongoing exits are expiry (§1.2) and the vol-spike
    stop (§3).

---

# PART 3 — TAIL-RISK HEDGE (constitution)

## 3.1 Primary: vol-spike STOP (measurable from the store NOW)

The short straddle is short gamma + short vega — unbounded loss on a vol spike. The
load-bearing tail protection is a vol-spike DE-RISK (close the short straddle), not
a static wing, because the store has ATM IV + DVOL but NOT the OTM skew a static
wing needs (F2).

Trigger (either leg, evaluated on every hourly DVOL/ATM-IV snapshot while in
position):

    vol_spike(t) = DVOL(t)/DVOL(entry) - 1 > VOL_SPIKE_PCT        # default +20%
                   OR atm_iv(t)/atm_iv(entry) - 1 > IV_SPIKE_PCT  # default +15%

On trigger: close the short straddle at the current mark (buy to cover both legs),
realizing the mark-to-market PnL (§1.2). This caps the vega/gamma loss at the
spike. VOL_SPIKE_PCT / IV_SPIKE_PCT are tunable and must be sensitivity-tested in
the backtest (the stop distance trades tail protection against whipsaw). FLAG F2a.

## 3.2 Alternative (flagged): static iron butterfly

Convert the short straddle into a short iron butterfly by buying OTM wings (long
OTM call + long OTM put) at strikes K±W. Net position = short ATM straddle + long
OTM strangle. This caps max loss at (W - net credit) per contract and needs NO
trigger. BUT it requires OTM IV (the skew), which the US-187 store does NOT have
(only ATM IV). To implement it the coder must either (a) assume a fixed skew
(e.g. wings priced at ATM IV + a constant skew premium — crude), or (b) extend the
store to capture OTM mark_iv per strike. FLAG F2b — this is a principal decision
(accept a skew assumption, or fund a store extension). Default = vol-spike stop
(§3.1) only; iron butterfly is deferred until skew data exists.

## 3.3 Net position (binding)

    Primary:  short ATM straddle + vol-spike stop (dynamic de-risk).
    Optional: + long OTM wings (iron butterfly) — only if F2b is signed off.

No naked short-vol is ever held without the vol-spike stop active. The stop is
MANDATORY, not advisory (mirrors the funding-carry directional hard stop).

---

# PART 4 — MARGIN MODEL

## 4.1 Margin (buying-power reduction)

Per the story: short-straddle margin >= premium + ~20% of underlying.

    margin_per_contract = premium_collected + MARGIN_UNDERLYING_FRAC * S0
    MARGIN_UNDERLYING_FRAC = 0.20        # ~20% of underlying (story-given)

FLAG F7: Deribit's real margin is PORTFOLIO margin (SPAN-like), not this simple
rule. The "premium + 20% underlying" is a CONSERVATIVE approximation for the
backtest. Live execution must use Deribit's actual initial-margin API, not this
constant. The approximation is fine for sizing/backtest; it is NOT a live margin
engine.

## 4.2 Sizing (1R = 1% capital, consistent with US-185)

The US-185 invariant is binding: 1R = 1% of capital, notional is the DEPENDENT
variable, risk_usd is re-derived from ACTUAL notional, and a capped position is
flagged (never silently shrink the labelled risk unit).

For a short straddle the "risk distance" is the assumed worst-case loss at the
vol-spike stop, expressed as a fraction of underlying notional:

    TAIL_LOSS_FRAC = 0.10     # assumed worst-case straddle loss as a fraction of
                              # underlying notional when the vol-spike stop fires
                              # (FLAG F6 — assumption, sensitivity-tested)

    risk_notional   = (CAPITAL_RISK_BUDGET * capital) / TAIL_LOSS_FRAC
                       # = 0.01*capital / 0.10 = 0.10*capital  (tail loss == 1R)
    margin_notional = (MARGIN_CAP_FRAC * capital) / margin_per_contract * S0
                       # margin deployed <= MARGIN_CAP_FRAC * capital
    notional        = min(risk_notional, margin_notional)
    contracts       = notional / S0
    margin_deployed = contracts * margin_per_contract
    risk_usd        = notional * TAIL_LOSS_FRAC     # re-derived from ACTUAL notional

    CAPITAL_RISK_BUDGET = 0.01   (reuse funding_carry's constant)
    MARGIN_CAP_FRAC     = 1.0    (no leverage; margin <= 1× capital)  FLAG F7b

Function surface (mirror funding_carry.size_position):

    def size_straddle(capital, S0, premium, tail_loss_frac=0.10,
                      margin_underlying_frac=0.20, margin_cap_frac=1.0) -> dict:
        # returns {notional, contracts, margin_deployed, risk_usd,
        #          size_capped, cap_reason, tail_loss_frac}

CRITICAL INVARIANT (same as US-185 §3.3): if the margin rail caps notional below
the risk budget, risk_usd is re-derived from the ACTUAL notional and size_capped
is set with the binding reason. The "R" label is never silently shrunk. Every
promotion record states risk_usd in dollars.

---

# PART 5 — BACKTEST + G3

## 5.1 Timed-vs-unconditional dominance test

For each historical day d (morning snapshot), compute the entry predicate (§2.1)
and the forward held-to-expiry net_pnl (§1.2). Build TWO trade sets:

  UNCONDITIONAL: short straddle every day (or every day with a valid ATM-IV row).
  TIMED:         short straddle only when enter_short_vol(d) is true.

Report, for each set: n, mean net_pnl, mean R (net_pnl / risk_usd), Sharpe
(annualized, deflated per US-183), profit factor, max drawdown, and the tail
statistics (worst 5% of trades, skew). The acceptance criterion is the story's:
TIMED Sharpe must be ~2–3× UNCONDITIONAL Sharpe, AND TIMED must survive G3 while
UNCONDITIONAL does not (or at least TIMED's pessimistic PF > 1.0 while
UNCONDITIONAL's is < 1.0). If TIMED does not dominate, the timing edge is not
real on this data and the strategy is NOT promotable.

## 5.2 Realistic fills + costs

Deribit options costs are DIFFERENT from the HL perp fees in fee_source.py (which
is HL-only). The strategy's own cost model (authoritative for the backtest):

    execution_cost = OPTION_TAKER_BPS/1e4 * S0 * contracts * 2 legs
                     + OPTION_SLIPPAGE_BPS/1e4 * S0 * contracts * 2 legs
    OPTION_TAKER_BPS    = 3.0    # Deribit options taker ~0.03% of underlying
    OPTION_SLIPPAGE_BPS = 1.0    # ATM straddle bid-ask, conservative

FLAG F4: these Deribit option fee constants are NOT in fee_source.py (which is
HL perp only). They must be VERIFIED against Deribit's live fee schedule (taker
~0.03% of underlying, maker rebate) before shipping, and ideally added to
fee_source.py as a third asset class ("option") so there is exactly one fee table.
Until then the constants above are the conservative default (fail-closed: taker,
no maker rebate credited).

## 5.3 G3 gate integration

The short straddle is crypto (Deribit BTC/ETH) but its timeframe is DAILY (morning
entry, held to expiry) — NOT 5m/1h/6h perps. So g3_gate.evaluate_fill_realism
routes it through the BAR-LEVEL hostile model (next-open entry + fee round-trip +
worst-print exit), NOT the L2 execution_sim path. The trade records fed to
assert_g3_gate must carry:

    asset_class = "crypto", timeframe = "1d"
    entry_price = S0, stop_price = the vol-spike stop level (S0 * (1 + IV_SPIKE_PCT
                  mapped to a price via the straddle's vega), or a conservative
                  tail-loss price), r_multiple = net_pnl / risk_usd.

FLAG F13 (cost double-counting): the strategy's r_multiple is ALREADY net of
Deribit option costs (§5.2), but g3_gate's bar-level model applies its OWN
compute_cost_drag using fee_source (HL perp fees). This DOUBLE-COUNTS costs, which
is fail-closed (conservative) but not clean. Resolution options: (a) accept the
double-count as a conservative floor (default), or (b) extend fee_source with the
"option" asset class so compute_cost_drag uses Deribit option fees. Default = (a);
(b) is a follow-up.

The G3 gate requires n >= 10, realistic mean R > 0, pessimistic PF > 1.0, and
realistic >= 0.60 × optimistic. Short-vol has negative skew (many small wins, a
few large losses), so the PESSIMISTIC leg (worst-print exit) is the binding test —
it is exactly where the vol-of-vol timing + vol-spike stop must prove they cut the
tail. The timed strategy must show FEWER tail losses than unconditional.

## 5.4 Minimum window + honest fallback (where history limits us)

The store just began accumulating (probe §0): DVOL ~30d, ATM IV = one snapshot.
A daily-entry short-vol backtest needs MULTIPLE vol regimes (calm + spike +
recovery) to (a) derive VOV_THRESHOLD (§2.2) and (b) meet G3's n >= 10 with a
meaningful tail sample. The research Sharpe 0.76–3.24 was on multi-year data.

MINIMUM WINDOW (binding): 6–12 months of DVOL + ATM IV + underlying bars, spanning
at least one full vol cycle. The ATM IV term structure (the premium side) is the
binding constraint — it is forward-only and cannot be backfilled from Deribit's
~30d endpoint.

HONEST FALLBACK (in order of preference):
  1. PAPER-FORWARD ACCUMULATION (default): run the strategy in PAPER (no live
     money) from now, writing every morning snapshot's vol-of-vol + ATM IV + the
     forward payoff to the store. After 6–12 months, run the §5.1 backtest and the
     §2.2 threshold derivation on the accumulated real data. Until then the
     strategy is a HYPOTHESIS, not promotable. This mirrors US-185 F3 (no
     historical mark/oracle series).
  2. LONGER DVOL BACKFILL (flagged): Deribit's get_volatility_index_data retains
     only ~30d, but DVOL has been published since 2021. A paid/alternative source
     could backfill DVOL (and possibly ATM IV) for a deeper backtest. FLAG F8 —
     requires a data-source decision + possibly cost.
  3. REALIZED-VOL PROXY (partial): the underlying 5m bars (hl_bar_store) are deeper
     than 30d, so realized_vol and the |S_T - K| payoff can be computed over a
     longer window. But the PREMIUM side (ATM IV) cannot — so this only extends the
     realized leg, not the full PnL. Not sufficient alone for G3.

The strategy CANNOT be G3-promoted until fallback 1 (or 2) produces the minimum
window. This is stated up front so no one fabricates a backtest on 30d of data.

---

## 6. Cross-cutting: resolved ambiguities, flags, implementation order

### 6.1 Ambiguities RESOLVED (with default)
  A1  Instrument -> short ATM straddle (BTC+ETH), BS-priced from the store (§1.1).
  A2  PnL identity -> held-to-expiry (primary) + mark-to-market (early exit) (§1.2).
  A3  Timing rule -> VOV_CALM AND VRP_RICH AND MORNING; threshold derived by
      quantile bucketing + CPCV, not a constant (§2).
  A4  Tail hedge -> vol-spike stop (measurable now); iron butterfly deferred (needs
      skew) (§3).
  A5  Margin -> premium + 20% underlying (approximation); sizing 1R = 1% capital,
      notional dependent, risk_usd re-derived (§4).
  A6  G3 route -> bar-level hostile model (timeframe "1d"), not L2 sim (§5.3).

### 6.2 Flags (need a decision / sign-off)
  F1   Instrument: ATM straddle (default) vs strangle (needs OTM IV). Sign-off only
       if strangle preferred.
  F2a  Vol-spike stop thresholds VOL_SPIKE_PCT=+20% / IV_SPIKE_PCT=+15% are
       defaults; sensitivity-test before shipping.
  F2b  Iron butterfly (static wings) needs OTM skew NOT in the store — accept a
       skew assumption, or fund a store extension. Deferred by default.
  F3   Universe: BTC+ETH only (store limitation). SOL = store extension, out of
       scope.
  F4   Deribit option fees (taker ~3bps, slip ~1bp) are NOT in fee_source.py (HL
       only). Verify against Deribit live schedule; ideally add an "option" asset
       class to fee_source.
  F5   Black-Scholes on coin-settled (inverse) Deribit options is approximate for
       greeks (mark_iv is exact; |S_T-K| payoff is exact).
  F6   TAIL_LOSS_FRAC = 0.10 (worst-case straddle loss at the stop) is an
       assumption; sensitivity-test.
  F7   Margin "premium + 20% underlying" is a conservative approximation; Deribit
       live margin is portfolio margin. Backtest-only.
  F7b  MARGIN_CAP_FRAC = 1.0 (no leverage). Risk-appetite call.
  F8   Longer DVOL/ATM-IV backfill needs a paid/alternative source (Deribit retains
       ~30d). Data-source + cost decision.
  F9   "Morning" hour: default 00:00 UTC (first DVOL candle of the day); 08:00 UTC
       is the alternative.
  F10  VRP_MULT = 1.0 (implied > realized); 1.1–1.2 is the conservative alternative.
  F11  Realized-vol bar interval: 5m bars (√105120 annualization) vs hourly
       (√8760). Default 5m.
  F12  r = 0 in Black-Scholes (crypto, no risk-free rate).
  F13  G3 cost double-counting (strategy's Deribit cost + g3_gate's HL cost_drag).
       Default: accept as conservative floor.
  F14  iv_store.py lives in scripts/data/ (not scripts/gauntlet/ as the story
       prompt stated). vol_of_vol_gate.py already imports it correctly. No action;
       documentation-only.

### 6.3 Implementation order (each a path-scoped green commit, py_compile clean)
  1. Shared BS helper: add _bs_price + _bs_vega (reuse options_recommender's
     _norm_cdf/_norm_pdf/_bs_d1) + unit tests (ATM straddle price ≈ 0.8·S·σ·√T).
  2. vol_vrp.py: straddle pricing + PnL identity (held-to-expiry + mark-to-market)
     + unit tests (golden vectors).
  3. vol_vrp.py: vol-of-vol timing predicate (VOV_CALM/VRP_RICH/MORNING) + the
     threshold-derivation routine (§2.2) + unit tests.
  4. vol_vrp.py: vol-spike stop + size_straddle (margin + 1R invariant) + unit
     tests (risk_usd == 1% capital when uncapped; re-derived when margin-capped).
  5. vol_vrp.py: simulate_vrp (daily walk, timed vs unconditional) + vrp_g3_record
     (mirror carry_g3_record) + the §5.1 dominance report.
  6. Paper-forward accumulation cron (no_agent, resolve_python.sh): write the
     morning vol-of-vol + ATM IV + forward payoff to the store daily. NO live
     money, NO promotion until the minimum window (§5.4) is met.

No edits to trades.csv / journal / publisher / universe.py / live capture /
funding_carry.py / fee_source.py (except the F4 "option" asset class, if signed
off) in any commit. universe.py is READ, not written.

END OF DESIGN.
