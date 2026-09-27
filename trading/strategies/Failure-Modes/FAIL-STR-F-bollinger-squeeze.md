---
type: failure-mode
strategy_id: STR-20260726-bollinger-squeeze-breakout-entry
strategy_name: Bollinger Squeeze Breakout
phase: 1A
verdict: KILL
reason: "Negative avg R (-0.048). Target hit rate only 2.0%. Squeeze condition too easily triggered."
metrics:
  r_expectancy: -0.048
  signals: 1466
  win_rate: 48.2
  sub_periods_positive: 0
lesson: "Bollinger Band squeeze as a breakout trigger produces too many false signals. The squeeze condition (lowest band-width in trailing 60 bars) is too common. Target rarely achieved (2.0% hit rate)."
data_limitations: "Daily bars, survivorship bias"
tags: [failure-mode, killed, bollinger, squeeze, breakout]
topic: strategies
confidence: high
has_quotes: false
source: HermesForge Strategies
---
# Failure Mode: STR-F Bollinger Squeeze

## What Failed

Volatility contraction (Bollinger Band squeeze) preceding expansion breakout. The squeeze condition is extremely common — nearly any low-volatility day registers as a local minimum.

## Root Cause

1. Squeeze condition too permissive (60-bar low in band-width is common)
2. 2:1 R:R target hit rate only 2.0% — breakouts rarely follow through
3. 80% of trades exit at time stop with barely positive R
4. Short side was a drag (long avg R +0.04 vs short -0.13)

## Lesson

- Volatility-breakout needs a stricter squeeze definition (prolonged, deep compression)
- 2:1 target is too ambitious for daily-bar breakouts
- Consider longer holding periods or trailing stops instead of fixed targets

## Related
- [[STR-F-phase1a]]
- [[STR-20260726-bollinger-squeeze-breakout-entry|STR-F Strategy]]
- [[REGIME-transitional]]

## Related Notes
- [[STR-20260726-bollinger-squeeze-breakout-entry|Bollinger Band Squeeze Breakout Entry]]
