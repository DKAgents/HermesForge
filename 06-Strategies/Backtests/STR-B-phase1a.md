---
type: backtest-result
strategy_id: STR-20260719-macd-histogram-divergence-weekly-assessment
strategy_name: MACD Histogram Divergence
phase: 1A
asset_class: stocks
direction: bidirectional
universe: 89 tickers
period_start: 2019-04-01
period_end: 2026-07-17
signals_per_year: 79
avg_r: 0.565
win_rate: 43.0
sub_periods_positive: "N/A (edge decaying)"
verdict: WATCH
verdict_reason: "Positive edge but decaying across periods (1.07R -> 0.42R -> 0.15R)"
data_limitations: "Daily bars, survivorship bias (current S&P constituents), frictionless"
produced_by: "[[Backtester]]"
tags: [backtest, phase1a, STR-B, stocks]
---

# STR-B Phase 1A Results

## Key Findings

- Edge decaying: 2019-21: 1.07R, 2022-23: 0.42R, 2024+: 0.15R
- Short signals weak in current bull market: 0.09R, 37% win rate
- Maturity 50+ bars underperforms vs 15-40 bars
- Time-stop exits (42% of trades) average 2.83R

## Phase 1B Perturbations

| Variant | Sig/Yr | Avg R | Win% | Status |
|---------|--------|-------|------|--------|
| Baseline | 79.7 | 0.554 | 42.4% | WATCH |
| Q2: Regime-aware direction filter | 59.2 | 0.714 | 44.5% | PASS |
| Q3: Maturity cap 40 bars | 55.2 | 0.634 | 43.4% | PASS |
| Combined best | 41.0 | 0.756 | 33.3% | WATCH |

## Related
- [[STR-20260719-macd-histogram-divergence-weekly-assessment|STR-B Strategy]]
- [[ADR-004-Phase1-Validation-Framework]]
- [[REGIME-trending]]
