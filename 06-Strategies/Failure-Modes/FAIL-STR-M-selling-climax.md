---
type: failure-mode
strategy_id: STR-20260726-selling-climax-reversal
strategy_name: STR-M Selling Climax Reversal
phase: 1A
verdict: KILL
reason: "All 6 signals stopped out (-1.000 avg R). Phase 1B with ATR stop + looser filters still negative (-0.212 best)."
metrics:
  r_expectancy: -1.000
  signals: 6
  win_rate: 0.0
  sub_periods_positive: 0
lesson: "Selling climax reversal pattern does not work as a per-stock mechanical scanner. The reversal-day low is too tight as a stop and ATR-based stops don't fix it. Murphy's selling climax describes market-wide capitulation, not per-stock dynamics. Per-stock reversals after multi-day declines in high-vol continue lower."
data_limitations: "Daily bars, survivorship bias"
tags: [failure-mode, killed, selling-climax, reversal, high-volatility]
---

# Failure Mode: STR-M Selling Climax

## What Failed

Selling climax reversal — buying after a multi-day decline when price makes a new low but closes above prior close, in high-volatility regime with heavy volume.

## Root Cause

1. Reversal day low as stop is too tight — 100% of signals stopped out in baseline
2. ATR-based stop (1.5x, 2x) doesn't help — price continues lower after the reversal bar
3. The selling climax pattern (N006, N162) describes market-wide capitulation, not per-stock dynamics
4. Per-stock multi-day declines in high-vol environments are more likely to continue than reverse
5. Loosening all filters (V6: vol 1.5x + 2-day decline + ATR 2x + 2:1 target) generated 33 signals but still -0.212 avg R

## Lesson

- Murphy's selling climax is a market-level pattern, not a per-stock scanner pattern
- Reversal-after-decline strategies in high-vol need a different mechanism (not just close-above-prior-close)
- The reversal day low is structurally a bad stop for this setup — it's the capitulation low, which gets re-tested
- High-volatility reversals require confirmation beyond a single bar's close

## Related

- [[STR-M-phase1a]]
- [[STR-20260726-selling-climax-reversal|STR-M Strategy]]
- [[REGIME-high-volatility]]
- [[N006-selling-climax-bottom-reversal-day]]