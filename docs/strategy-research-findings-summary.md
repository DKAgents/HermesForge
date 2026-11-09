# HermesForge Strategy Research — Full Findings & Conclusions

*Prepared for independent critical review. Self-contained: no prior context assumed.*

---

## 1. What this is

HermesForge is a systematic crypto trading-research pipeline on Hyperliquid (HL), a fully
on-chain perpetuals DEX. Over several weeks it ran an **exhaustive, disciplined search** for a
productive trading strategy. This document records what was tested, what was found, and the
conclusion. The central claim, stated plainly up front: **after testing every retail-accessible
signal class, the only real, persistent, net-positive edge found is a delta-neutral funding
carry (~10–15% unlevered APR, maker-only). There is no signal-based "alpha" in this market.**

---

## 2. Methodology — the gauntlet (8 gates) and the honesty discipline

Every hypothesis runs through an 8-gate gauntlet, cheapest first:

| Gate | Test |
|---|---|
| G0 | Cost + capacity pre-screen (gross must clear ~4× all-in cost; taker 4.5 bps/leg, ~12 bps round-trip) |
| G1 | Signal scan on a liquidity-filtered universe |
| G2 | Leakage audit (look-ahead, funding/OI lag) |
| G3 | Execution realism — optimistic (mid) / realistic (queue-aware) / pessimistic (taker + adverse) fills |
| G4 | Combinatorial Purged Cross-Validation (CPCV, N=12/k=2, 66 splits) — 10th-pct fold PF ≥ 1.0 |
| G5 | Multiple-testing correction — Deflated Sharpe ≥ 0.95, PBO ≤ 0.30 |
| G6 | Robustness partitioning (regime, beta cluster, funding) |
| G7 | Forward validation (paper trades) |

**Non-negotiable discipline applied throughout:**
- **Pre-registration** — every hypothesis documents the mechanism, counterparty, falsification
  rule, and expected effect size *before* any backtest; results are recorded in an append-only
  trials ledger (hash-chained, ~150+ trials) that feeds the G5 multiple-testing correction.
- **No look-ahead** (signal at bar close → fill next open), **no leverage**, **LIVE off** throughout.
- **Cost is charged** on both legs; results are always gross → net, never gross alone.
- **Zero-drift synthetic controls** to separate a real signal from a geometric artifact.
- **Leading-vs-echo tests** (does the signal *predict* forward return, or merely *correlate*
  contemporaneously?).
- **Funding-vs-basis decomposition** (a "funding edge" that is actually mark-oracle basis is
  reported as basis, never claimed as funding).
- **Fill-realism before any promotion** — a strategy is never promoted on mid-price or
  close-entry fills.

---

## 3. What was tested, and the result

### 3.1 Price timing / technical analysis — NULL
Chart patterns, ICT/SMC "liquidity sweeps", and oscillator-extreme mean-reversion (a
CCI-family "Eufearia Pro 7" indicator a user brought from TradingView).
**Result:** all null. Win rates are coin-flips for their R:R (~25% at 3:1), measured identically
long and short; oscillator oversold-bounce has t<1 and a negative median; the "liquidity-grab /
stop-hunt" mechanism itself is empirically false (broker stops aren't visible to the auction).

### 3.2 Positioning — open interest — NULL
HYP-16: "high relative OI → big subsequent move." Tested direct (top-decile OI) and via funding
proxies.
**Result:** ratio 1.002, p=0.46 — no move expansion. Stable across a pre-registered robustness
sweep (80/90/95th pct × SMA20/50); a bare trend filter captured the full effect, OI's marginal
contribution ≈ 0. Rejected robustly.

### 3.3 Positioning — funding / cross-sectional OI — NULL
HYP-20/21/22: funding-extreme positioning, cross-sectional OI-change momentum, funding-crowd
following, and a multifactor composite.
**Result:** the cross-sectional OI-level signal was real in direction (corr 0.13 vs price
momentum, +11–13 bps gross) but **too thin vs turnover cost** — "cost, not signal, is the binding
constraint." The multifactor composite cleared cost at 5d (+48 bps net) but failed robustness
(DSR 0.33, PBO 0.39, non-overlapping n=178). Funding-crowd-following paid more carry than it
earned (net negative at every horizon). All closed.

### 3.4 Momentum — NULL (one decaying real effect)
Symmetric cross-sectional momentum, and a regime-conditioned version.
**Result:** symmetric momentum is null. BUT leg decomposition found a real one-sided effect:
**"short the momentum losers"** (+0.20R above the zero-drift geometric control — losers keep
decaying). This survived a liquidity/shortability floor and G3 fill-realism — the *first*
structure to get that far — but it **decays**: year-by-year net R +0.125 → +0.105 → +0.187 →
+0.071, and it failed robustness (G4 10th-pct PF 0.72, DSR 0.84, PBO 0.52). A real signal being
arbitraged away.

### 3.5 R:R target ratio (a methodology finding, not an edge)
HYP-23, testing the coach's "prefer 3:1 R:R" claim — same signal + stop, only the target moved.
**Result:** net expectancy *rises* 1R→3R, but for two reasons that are **not** alpha: (a) a tight
target is a *fee tax* on a positive-drift signal (fixed fee chops the drift), and (b) percentage
stops on log-normal crypto give far targets a *geometric* gain at zero alpha (a zero-drift
control reproduced it). "Wider targets let a real drift compound" is risk-management, not edge.

### 3.6 Liquidation flow — NULL (both horizons)
HYP-26 (daily) + HYP-27 (intraday), using newly-acquired forced-liquidation data ($58.7B notional,
2.85M events, 8M fills over 17 months).
**Result:** forced *selling* is followed by **reversal** (exhaustion — the "long-squeeze bottom"),
not continuation, at every horizon; the "liquidation cascade" narrative is empirically false. The
one continuation (short squeezes, forced *buying*) is real but ~half an execution cost. |IC| ~0.02,
too thin. Closed at both daily and intraday.

### 3.7 Order-flow imbalance (CVD) — NULL for a taker
HYP-34: cumulative aggressive-buy−sell delta → short-horizon continuation.
**Result:** positive gross, negative net at every horizon (taker cost). Order-flow imbalance is
the **market-maker's** edge, not a taker's — exactly as the prior expected.

### 3.8 Crowd long/short ratio (contrarian positioning) — DATA-GATED
HYP-33: fade the extreme retail crowd. **Result:** the free OKX history is only ~6 months
(hard-capped, not truncated) — too short for a robust contrarian test. Reported data-gated, no
test on an inadequate window (which would manufacture noise-as-signal). Testable ~mid-2027 via
forward accumulation.

### 3.9 On-chain / stablecoin flow — NULL (echo, not lead)
HYP-32: aggregate stablecoin supply + TVL growth → subsequent price.
**Result:** the flow metrics **correlate with** price (they rise in bull markets) but do **not
lead** it — the leading-vs-echo test failed (echo IC 2.4× the forward IC). A coarse trend
artifact, not a "capital-mints-then-bids" lead. Any real on-chain signal would be at per-coin
exchange-netflow level, which is paid-tier and not pursued.

### 3.10 Cross-venue basis — DOMINATED (not additive)
HYP-31: HL-vs-OKX funding spread + price basis.
**Result:** the HL-only carry already hedges with *free* HL spot; going cross-venue replaces that
with a long OKX perp that *pays* funding itself, netting the "spread" down to ~2.6–3.7pp while
adding a second venue's fees + transfer risk. Price basis is market-maker-arbitraged to ~1bp.
Cross-venue is a strictly worse version of the carry we already have.

### 3.11 Variance risk premium (options) — RETIRED
HYP-30: sell ATM straddles on BTC/ETH (data backfilled free from Deribit's public History API,
years deep).
**Result:** the premium is real but **co-locates with the tail** — a single vol spike gives back
more than a year of premium (max DD −81% to −449%). The "sell in calm vol" gate was *backwards*
(calm vol = thin premium = negative; spiking vol = fat premium = eaten by the spike). No free
lunch, and not diversifying vs the carry (both are short-risk-premia concentrated in the same
vol-spike tail).

### 3.12 Copytrading reverse-engineering — NO COPYABLE ALPHA
Pulled the HL leaderboard (38k+ public trader accounts), stored top-50 fill history, screened out
"gain harvesters" (realize winners / hold losers — a trader with 1,258 wins/4 losses was pure
harvesting artifact), then reverse-engineered the genuine top traders' fills.
**Result:** the money resolves to five archetypes, none of which is copyable signal-alpha:
directional **thesis-holders** (short-crypto-in-a-downtrend = beta + timing), **market makers**
(98–99.5% maker fills = spread/rebate infra), **time-scheduled bots** (long-ETH-daily = pure
beta; short-high-funding-memes = *our carry*), **buy-and-hold**, and **arb/MEV**. The single
"clean mechanical rule" found (short an xyz index-perp in a 13–15 UTC window, claimed 75.6%/5.2:1)
**did not reproduce** (46.8% win, negative median, fat right tail) and had no identifiable
mechanism — a fill-sample artifact.

---

## 4. The one positive result — the delta-neutral funding carry

**This is the single real, persistent, net-positive edge.** Details:

- **Trade:** short the perp + hold the spot (delta-neutral cash-and-carry) on BTC/ETH/SOL, where
  liquid spot exists. The hedge is HL spot (free); cross-venue is dominated (3.10).
- **Mechanism (the load-bearing insight):** HL's *structural base funding floor* — 1.25e-5/hr =
  **10.95% APR** — is always-on. This is a **base-yield carry** ("lend the majors at ~15%"), *not*
  a "fade the over-leveraged crowd" signal. That is *why* it is persistent, not decaying.
- **Return:** ~15–21% unlevered APR at optimistic/maker fills; **~10–12% conservative** after
  realistic maker fills; **taker survives but degrades** (~+10–19%).
- **Constraints:** **maker-only is mandatory** (taker fills are decisively net-negative, −7% to
  −14%). No leverage. Delta-neutral only on the majors.
- **Capacity:** ~$24.5M (conservative 0.5%-of-daily-volume rail) — finite, not pocket-sized.
- **Risks (honestly priced):** hedge basis drift (mark−oracle, fat-tailed — |basis|>10bps on
  6–10% of hours), exchange/custody, churn forced-fill (39–56% of gross — the dominant drag).
- **Status:** paper-forward (running hourly, maker-only, funding-vs-basis split recorded), with a
  documented go-live checklist. The *funding* component is validated on ~17 months; the spot-basis
  hedge is forward-accumulating (the one assumed input — the live spot spread — still to confirm).

---

## 5. Methodology lessons learned (corrections that changed results)

1. **A cost-model error** (writing a 45bps gross-target as a *per-leg* fee instead of the real
   4.5bps/leg) over-rejected a marginal edge ~7.5× — fixed, and the corrected result still failed
   robustness, so nothing material was masked.
2. **Overlapping returns inflate significance ~5×** — a daily-rebalanced 5d-hold series had n=886
   where the honest non-overlapping n was 178; the mean is unbiased, its t-stat is fake.
3. **Zero-drift controls are mandatory** — far-target gains and "winner" legs can be pure
   log-normal geometry with zero alpha.
4. **Leading ≠ coincident** — on-chain flow and TVL *correlate* with price without *predicting* it.
5. **Realized ≠ true** — the copytrading screener's realized-PnL ranking was inflated by gain
   harvesting until crossed against unrealized PnL.
6. **Fill-realism is the promotion gate** — a strategy that only profits on mid-price fills is a
   fill fantasy; several strategies died exactly there.
7. **Edges decay** — the one real signal (short-the-losers) is being arbitraged toward zero; the
   carry persists *because* its mechanism is a structural floor, not a signal.

---

## 6. Conclusions

1. **There is no signal-based alpha in retail-accessible crypto.** Every price, positioning, flow,
   and options signal class tested null — either absent (flat nulls), too thin vs cost, or a
   coincident echo. This was confirmed *twice*, from independent directions: the exhaustive search
   *and* the top traders' public fills (which resolve to beta + market-making + MEV, not alpha).
2. **The edges that exist are structural** — carry, spread/maker-rebate, MEV — and they are either
   harvestable (the funding carry) or not copyable by a retail taker (market-making infra).
3. **The funding carry is the one tradeable edge** — ~10–15% unlevered, maker-only, ~$24.5M
   capacity, persistent because it is a structural funding floor rather than a signal.
4. **The VRP is real but un-harvestable** — its premium co-locates with the tail it compensates.
5. **The systematic search is complete** — further hunting for a high-return signal strategy has
   no evident path; the recommendation is to deploy the carry (yield) and treat discretionary
   trading as the only active-alpha layer.

---

## 7. Current state

- Funding carry: **paper-forward**, hourly, maker-only, funding-vs-basis split, with a committed
  go-live checklist (the path to real money is the carry, deployed small first).
- The search is effectively closed; the finding is stable and, now, doubly confirmed.
