---
type: backtest-result
strategy_id: STR-20260726-rsi-mean-reversion-entry
strategy_name: RSI Mean-Reversion
phase: 1A
asset_class: stocks
direction: bidirectional
universe: 216 tickers
period_start: 2019-04-01
period_end: 2026-07-17
signals_per_year: 1666.7
avg_r: -0.056
win_rate: 40.6
sub_periods_positive: "0/3"
verdict: KILL
verdict_reason: "Negative avg R (-0.056), 0/3 sub-periods positive. No edge exists."
data_limitations: "Daily bars, survivorship bias, frictionless"
produced_by: "[[Backtester]]"
tags: [backtest, phase1a, STR-E, stocks, kill]
---

# STR-E Phase 1A Results

## Exit Breakdown

| Exit | Count | % |
|------|-------|---|
| Stop | 5,612 | 46.6% |
| Time | 4,790 | 39.8% |
| Target | 1,640 | 13.6% |

Stop hit far more often than target. Mean-reversion entries fading moves that continue rather than reverting.

## Related
- [[FAIL-STR-E-rsi-mean-reversion]]
- [[STR-20260726-rsi-mean-reversion-entry|STR-E Strategy]]
- [[REGIME-trending]]
