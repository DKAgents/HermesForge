# HYP-37 — Time-series trend on majors, volatility-targeted (sleeve alongside carry)

Date: 2026-11-09 (UTC)
Owner: backtester (HermesForge swarm)
Pre-registration: `trading/strategies/Hypotheses/HYP-37-trend-sleeve.md`
Backtest: `scripts/gauntlet/backtest_hyp37_trend_sleeve.py`
Directive cross-reference: **directive §8 "HYP-33" == HYP-37** (renumbered — HYP-33 = crowd
long/short, HYP-36 = Polymarket; next free ID taken, append-only ledger preserved).

## TL;DR — FALSIFIED at maker cost

A vol-targeted 20/60/120-day time-series trend on BTC/ETH/SOL does **not** survive the amended
gates. The signal has no predictive content (IC ≈ 0 at every horizon 1–20d), the 10th-percentile
CPCV fold PF is 0.71–0.82 (< 1.0), and DSR is 0.33–0.44 (≪ 0.95) even under the most generous
M-6 family accounting (N=7). Its +6%/yr headline CAGR is diluted long-beta, not alpha: the
risk-adjusted return (Sharpe 0.49) is *below* plain buy-and-hold BTC (0.53) on the same window.
As a sleeve alongside the carry it is a **drag, not a diversifier**: correlation ≈ 0.02, and a
50/50 combination turned *negative* (−2.2%/yr) over the 13.5-month funding-overlap window while
adding −18% of drawdown to the carry's −0.6%.

## What was tested (pre-registered, fixed)

| Item | Setting |
|---|---|
| Universe | BTC, ETH, SOL daily (2020-08-19 → 2026-11-08, ~2273 bars; SOL from 2020-09-14) |
| Trend signal | s = 0.5·log(close/closes₋₂₀) + 0.3·log(close/closes₋₆₀) + 0.2·log(close/closes₋₁₂₀) |
| Vol forecast | HAR-RV: 0.25·rv_d + 0.35·rv_w(5d) + 0.40·rv_m(21d), rv = squared daily log-return |
| Vol target | 20% ann.; scale = min(1.0, σ_daily/σ̂); **no leverage** (cap 1.0) |
| Position | long/flat and long/short; maker and taker (M-2 cost symmetry) |
| M-3 buffer | sign hysteresis — flip direction only when |s| ≥ round-trip cost (maker 6 bps / taker 12 bps) |
| Cost | per-leg txn = fee + slip/2 (maker 2.75, taker 5.75 bps); charged on |Δw| |
| Sampling | **non-overlapping** throughout (weekly blocks for CPCV/DSR; stride-h for IC) |

Maker/taker fee schedule from `fee_source` (base tier): perp maker 1.5 / taker 4.5 bps, slip 2.5.

## Result 1 — M-7 IC-by-horizon: no predictive content

corr(trend_score_t, forward h-day return), non-overlapping (stride-h):

| h | IC | t | p | n |
|---|---|---|---|---|
| 1d | +0.005 | +0.23 | 0.82 | 2126 |
| 2d | +0.011 | +0.37 | 0.71 | 1063 |
| 3d | +0.012 | +0.31 | 0.76 | 708 |
| 5d | +0.021 | +0.43 | 0.66 | 425 |
| 10d | +0.005 | +0.07 | 0.95 | 212 |
| 20d | −0.002 | −0.02 | 0.98 | 106 |

Every horizon is statistically indistinguishable from zero (max |IC| = 0.021, all p ≫ 0.05). The
"slow information diffusion → trend predicts forward return" mechanism does **not** show up in the
data over 6+ years. This is the load-bearing null: no sizing/buffering can manufacture edge from a
null IC.

## Result 2 — M-2 maker vs taker (net of fee + slippage, portfolio equal-weight)

| Variant | CAGR | Sharpe | maxDD | turnover |
|---|---|---|---|---|
| long/flat maker | +6.23%/yr | +0.49 | −22.2% | 115× |
| long/flat taker | +5.47%/yr | +0.44 | −23.5% | 114× |
| long/short maker | +5.05%/yr | +0.35 | −32.2% | 217× |
| long/short taker | +3.62%/yr | +0.28 | −34.5% | 215× |

M-2 cost symmetry is satisfied in direction — maker is uniformly better than taker (long/flat
+0.76%/yr, long/short +1.43%/yr) — but the *level* is not: maker Sharpe is still 0.35–0.49, below
buy-and-hold BTC (0.53) and ETH (0.35)/SOL (0.48) on the same window. The positive CAGR is the
bull-market beta the vol-target happened to hold, diluted to a 20% vol target (~0.27–0.48 average
gross), not timing alpha. The long/short variant is strictly worse (whipsaw costs on both sides,
Sharpe 0.35).

## Result 3 — G4 CPCV + G5 DSR (non-overlapping weekly blocks, n=426)

| Variant (maker) | 10th-pct PF | median PF | PBO | DSR (M-6, N=7) | DSR (N=137) | DSR (N=168) |
|---|---|---|---|---|---|---|
| long/flat | 0.710 | 1.140 | 0.38 | 0.441 | 0.361 | 0.365 |
| long/short | 0.818 | 1.124 | 0.41 | 0.374 | 0.335 | 0.341 |

Both falsification triggers fire, and the verdict is **robust to the M-6 accounting choice**: the
DSR is 0.33–0.44 whether deflated by the 7-family trend subset (M-6), the 137 distinct IDs, or the
full 168 rows. The 10th-pct fold PF is < 1.0 in every variant. (PBO 0.38–0.41 is not used as a
kill signal here — per US-06 it is a known single-strategy rank-scatter artifact.)

## Result 4 — M-5 minimum detectable effect

Observed weekly Sharpe (maker) = +0.055 (long/flat) / +0.041 (long/short). MDE Sharpe = 0.24 at
n=426 non-overlapping weeks and N=7 family trials. **"Not detected above MDE Sharpe = 0.24"** — the
trend is not merely below the promotion bar; it is below the floor a *single* undeflated test could
reliably see (per-week Sharpe 0.05 ⇒ t ≈ 1.1, indistinguishable from zero with no correction at all).

## Result 5 — Sleeve vs the carry (real HL funding, overlap 2025-09-27 → 2026-11-08, 407d)

| Metric | Sleeve (long/short, maker) | Carry (gross funding) | 50/50 combined |
|---|---|---|---|
| CAGR | — (Sharpe −0.38) | ~4.4% APR | **−2.18%/yr** |
| Sharpe | −0.38 | +11.98 | −0.16 |
| maxDD | −18.4% | −0.6% | −8.1% |

- **correlation(sleeve, carry) = +0.019** — near zero by construction (carry is delta-neutral and
  near-constant; the trend is directional), so the trend adds no diversifying variance reduction.
- **The trend sleeve LOST money over this window** (Sharpe −0.38), so combining it 50/50 with the
  carry turned a positive carry into a −2.2%/yr portfolio. It is a return drag and a drawdown adder,
  not a sleeve worth adding.
- **Funding interaction:** the sleeve's signed funding P&L was +23.9 bps (BTC +92.7, ETH +60.2,
  SOL −81.2) — +4.8% of the carry's gross, i.e. the trend sleeve does not materially cannibalize the
  carry's funding harvest (its shorts roughly offset its longs). The harm is directional losses, not
  funding leakage.

## Falsification verdict

At maker cost (M-2), on non-overlapping samples, with M-3 buffering, M-5 MDE, M-6 family
accounting and M-7 horizon structure applied:

- **G4**: 10th-percentile fold PF 0.71 / 0.82 < 1.0 → **FAIL**.
- **G5**: DSR 0.441 / 0.374 < 0.95 (at the generous M-6 family count N=7) → **FAIL**.
- **M-7**: IC indistinguishable from zero at every horizon 1–20d → **no mechanism**.
- **Sleeve**: correlation ≈ 0, combined 50/50 negative, adds −18% drawdown → **not additive**.

**NOT PROMOTED.** Trend-following on the majors is not the "one remaining price signal" — it is a
null like every other price signal the program has tested, and maker execution does not rescue it.

## Honesty notes (recorded, not a re-tune)

1. **Vol-forecast noise.** The HAR-RV daily component (25% weight on a single daily r²) is noisy
   (vol forecast σ/μ ≈ 50%), so daily vol-targeting churns ~30×/yr on scale changes alone, costing
   ~3%/yr at maker rates. A smoother RV estimator (intraday RV, Parkinson high-low) would cut this,
   but it **cannot create edge where IC ≈ 0** — the null is in the signal, not the sizing.
2. **M-3 buffer is sub-scale.** The 6-bps round-trip band suppresses only zero-crossing whipsaw
   (87 flips over 6.2y); it is ~100× too small to suppress the vol-scale micro-rebalancing. A fuller
   size-band would reduce turnover but not change the verdict.
3. **Funding is unmodeled in the headline net** (fee + slippage only); the signed funding P&L is
   reported separately from real HL funding on the overlap window (+4.8% of carry gross). Realized
   carry funding this window is ~4.4% APR equal-weight (BTC ~6.3%), below the 10.95% anchor, because
   funding dips below (and sometimes below zero) the anchor in risk-off — consistent with the
   directive's §3 correction ("strong tendency, not a floor").
4. **The carry remains the program's one positive edge.** This test was the trend *sleeve's*
   falsification, not a re-test of the carry; the carry's own numbers are restated on total capital
   under the C-1/C-2/C-3 fixes, separately.

## Ledger

Trial appended (hash-chained): `HYP-37`, param_hash `b5d8dc28…`, chain intact (169 trials,
`verify_integrity` = OK). Result recorded with `promote = {long/flat: false, long/short: false}`.
