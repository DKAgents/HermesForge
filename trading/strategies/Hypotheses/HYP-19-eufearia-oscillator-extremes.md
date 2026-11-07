---
hypothesis_id: HYP-19
source: human (TradingView indicator — EUFEARIA Pro 7, user-provided)
venue: hyperliquid
instruments: BTC, ETH, SOL + top-25 HL perps by liquidity
horizon: daily bars; hold until opposite signal or time-stop
entry: LONG when oscill crosses ABOVE its signal line while oscill <= oversold (-50, or adaptive 5th pct); SHORT/flat analog when oscill crosses BELOW signal while >= overbought (+50, or adaptive 95th pct)
exit: opposite cross, or N-bar time stop
expected_gross_edge_bps: claimed positive (LOW/HD anecdote); measured, not assumed
cost_hurdle_bps: 45 (single-leg 4x taker)
data_dependencies: HL 1d bars (~4y, 31 coins)
counterparty: NONE IDENTIFIABLE — a mean-reversion oscillator trader has no structural loser on the other side; the spread-earning maker is not structurally losing to a discretionary timing rule.
topic: general
confidence: high
has_quotes: false
tags: []
---
# HYP-19 — EUFEARIA-pro mean-reversion oscillator extremes (daily)

## Source & decode

User-provided PineScript "EUFEARIA Pro 7" — a CCI-style normalized-deviation
oscillator (`ci = (hlc3 − ema(hlc3,10)) / (0.015 · ema(|dev|,10))`, then
`osc = ema(ci,21)`, `sig = sma(osc,4)`). Signal = buy the oversold bounce /
sell the overbought top, with divergence + direction-turn filters. This is a
mean-reversion oscillator-extreme timing signal.

## Prior (recorded BEFORE testing)

Retail-TA oscillator / reversal-timing signals carry a heavy NEGATIVE prior:
reversal detectors are coin-flips at their R:R, and classic oscillator OOS edges
sit below realistic friction. HYP-18 (trend+pullback+momentum scalp) already
failed G0 on this exact family. The LOW/HD "significant gains" is a 2-stock
anecdote, not measured expectancy.

## Pre-registered operationalization (fixed)

- oscillator `osc` = ema( normalized(hlc3 − ema10) , 21 ); signal `sig` = sma(osc, 4).
- LONG entry: crossup(osc, sig) AND osc <= oversold. EXIT: crossdown(osc, sig)
  or 20-bar time stop.
- SHORT entry (if the universe permits a directional short): crossdown above
  overbought. Kept optional; primary test is long-only (matches the indicator's
  "buy the fear" emphasis).

## Falsification (kill rules)

- G0 KILL: median daily |move| after entry < 4x all-in taker cost → fast-fail.
- G3 KILL: net R <= 0 under realistic/pessimistic fill → fill fantasy / coin-flip.
- Escalate to G4/G5 only if it survives both; then CPCV 10th-pct PF >= 1.0,
  DSR >= 0.95, PBO <= 0.30.

## Note

Counterparty is honestly "none identifiable" — that absence is the structural
reason oscillator timing is expected to fail, not a data quirk. Higher-TF (daily)
is correctly low-friction; the question is whether the signal has any edge at
all, which the gauntlet measures, not the LOW/HD picks.