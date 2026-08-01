---
type: failure-mode
strategy_id: STR-20260728-adaptive-trend
strategy_name: AdaptiveTrend (Crypto)
phase: 1B/2
verdict: KILL
reason: "Sharpe 0.151, MDD -38.9%. Daily bars insufficient for crypto momentum. Paper edge requires 6h bars."
metrics:
  sharpe: 0.151
  annual_return: 1.6
  max_drawdown: -38.9
  win_rate: 32.4
  trade_count: 373
lesson: "Timeframe mismatch is structural, not parametric. The paper's Sharpe 2.41 was on 6h bars; daily bars (Sharpe 1.63 per paper ablation) lose the intraday momentum signal. No parameter tuning can fix this."
data_limitations: "Daily bars only. 6h data available but only ~13 months deep, insufficient for backtesting."
tags: [failure-mode, killed, crypto, timeframe-mismatch, STR-I]
---

# Failure Mode: STR-I Crypto on Daily Bars

## What Failed

AdaptiveTrend strategy applied to crypto with daily bars. The strategy works well on stocks (Sharpe 0.815) but fails on crypto (Sharpe 0.151) because the edge depends on 6-hour bar granularity.

## Root Cause

1. Paper's edge depends on 6h bars (Sharpe 2.41 on H6 vs 1.63 on D1)
2. Crypto momentum signals are shorter-lived than daily bars can capture
3. Daily bars miss intraday momentum that drives the entry signal
4. 6h data available from Hyperliquid but only ~13 months deep — insufficient for backtesting

## Lesson

- Timeframe matters more than parameters for momentum strategies
- Don't assume a strategy transfers across timeframes without testing
- 6h crypto data needs >3 years of history before serious backtesting

## Related
- [[STR-I-phase1b2-crypto]]
- [[STR-I-phase1b2-stocks]]
- [[STR-20260728-adaptive-trend|STR-I Strategy]]
