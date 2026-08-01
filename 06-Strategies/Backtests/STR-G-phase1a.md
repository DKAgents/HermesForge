---
type: backtest-result
strategy_id: STR-20260726-relative-strength-sector-rotation-entry
strategy_name: Relative Strength Sector Rotation
phase: 1A
asset_class: stocks
direction: long-only
universe: 216 tickers
period_start: 2019-06-11
period_end: 2026-07-17
signals_per_year: 1243.8
avg_r: 0.105
win_rate: 52.2
sub_periods_positive: "0/3"
verdict: KILL
verdict_reason: "Avg R 0.105 < 0.2 kill threshold. Extremely high signal count but razor-thin edge."
data_limitations: "Daily bars, survivorship bias, frictionless"
produced_by: "[[Backtester]]"
tags: [backtest, phase1a, STR-G, stocks, kill]
---

# STR-G Phase 1A Results

## Exit Breakdown

| Exit | Count | % |
|------|-------|---|
| Time | 6,277 | 71.1% |
| Stop | 2,062 | 23.4% |
| Target | 491 | 5.6% |

Only 5.6% reach the 2.5:1 target. RS-crossover condition triggers too easily by short-term noise.

## Related
- [[FAIL-STR-G-relative-strength]]
- [[STR-20260726-relative-strength-sector-rotation-entry|STR-G Strategy]]
