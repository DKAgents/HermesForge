---
type: failure-mode
strategy_id: STR-20260726-first-pullback-trend-swing
strategy_name: First Pullback Trend Swing
phase: 1A
verdict: KILL
reason: "Only 3 signals in 7 years (0.9/yr). All 3 stopped out. Filter stack too restrictive."
metrics:
  r_expectancy: -1.975
  signals: 3
  win_rate: 0.0
  sub_periods_positive: 0
lesson: "Confirmation-candle + EMA-zone + volume-contraction + ADX + RSI filter stack compounds too severely. Discretionary-style multi-filter approaches don't work as mechanical scanners."
data_limitations: "Daily bars, survivorship bias"
tags: [failure-mode, killed, pullback, trend-swing, filter-stack]
topic: strategies
confidence: high
has_quotes: false
source: HermesForge Strategies
---
# Failure Mode: STR-H First Pullback

## What Failed

First pullback to 50-day MA in an established trend, confirmed by candle pattern + EMA zone + volume contraction + ADX + RSI. The filter stack was so restrictive that only 3 signals fired in 7 years.

## Root Cause

1. Too many filters compounded — each filter reduces signal count multiplicatively
2. Confirmation candle requirement is the primary bottleneck
3. Discretionary-style multi-filter approaches don't translate to mechanical scanning
4. Even when signals fired, all 3 were losers

## Lesson

- Limit to 2-3 filters max for mechanical scanners
- Test signal frequency early before adding more filters
- Discretionary trading patterns need simplification before automation

## Related
- [[STR-H-phase1a]]
- [[STR-20260726-first-pullback-trend-swing|STR-H Strategy]]
- [[REGIME-trending]]
