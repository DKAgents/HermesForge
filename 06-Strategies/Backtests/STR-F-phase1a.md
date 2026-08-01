---
type: backtest-result
strategy_id: STR-20260726-bollinger-squeeze-breakout-entry
strategy_name: Bollinger Squeeze Breakout
phase: 1A
asset_class: stocks
direction: bidirectional
universe: 216 tickers
period_start: 2019-04-01
period_end: 2026-07-17
signals_per_year: 209.7
avg_r: -0.048
win_rate: 48.2
sub_periods_positive: "0/3"
verdict: KILL
verdict_reason: "Negative avg R (-0.048). Target hit rate only 2.0%. 80% exit at time stop."
data_limitations: "Daily bars, survivorship bias, frictionless"
produced_by: "[[Backtester]]"
tags: [backtest, phase1a, STR-F, stocks, kill]
---

# STR-F Phase 1A Results

## Key Finding

Target-hit rate only 2.0% — the 2:1 R:R target essentially never resolves. 80% of trades exit at the 10-bar time stop with barely positive avg R (+0.16).

## Related
- [[FAIL-STR-F-bollinger-squeeze]]
- [[STR-20260726-bollinger-squeeze-breakout-entry|STR-F Strategy]]
- [[REGIME-transitional]]
