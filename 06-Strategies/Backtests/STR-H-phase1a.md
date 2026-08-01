---
type: backtest-result
strategy_id: STR-20260726-first-pullback-trend-swing
strategy_name: First Pullback Trend Swing
phase: 1A
asset_class: stocks
direction: long-only
universe: 216 tickers
period_start: 2019-04-01
period_end: 2026-07-17
signals_per_year: 0.9
avg_r: -1.975
win_rate: 0.0
sub_periods_positive: "0/3"
trade_count: 3
verdict: KILL
verdict_reason: "Only 3 signals in 7 years (0.9/yr). All 3 stopped out. Filter stack too restrictive."
data_limitations: "Daily bars, survivorship bias, frictionless"
produced_by: "[[Backtester]]"
tags: [backtest, phase1a, STR-H, stocks, kill]
---

# STR-H Phase 1A Results

## Key Finding

Only 3 signals across 216 tickers over ~7 years. All 3 stopped out (AIG -3.75R, GOOGL -1.11R, PRU -1.07R). The confirmation-candle + EMA-zone + volume-contraction + ADX + RSI filter stack compounds so severely that almost no bar satisfies all gates.

## Related
- [[FAIL-STR-H-first-pullback]]
- [[STR-20260726-first-pullback-trend-swing|STR-H Strategy]]
- [[REGIME-trending]]
