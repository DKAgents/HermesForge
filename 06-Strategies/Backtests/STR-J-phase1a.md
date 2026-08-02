---
type: backtest-result
strategy_id: STR-20260726-eufearia-cci-reversal
strategy_name: EUFEARIA CCI Reversal
phase: 1A
asset_class: stocks
direction: bidirectional
universe: 529 tickers
period_start: 2019-04-01
period_end: 2026-07-17
signals_per_year: 3488
avg_r: 0.017
win_rate: 32.8
sub_periods_positive: "2/3"
verdict: KILL
verdict_reason: "Avg R 0.017 < 0.2 kill threshold. Baseline bidirectional fails."
data_limitations: "Daily bars, survivorship bias, frictionless"
produced_by: "[[Backtester]]"
tags: [backtest, phase1a, STR-J, stocks, kill-baseline]
topic: strategies
confidence: high
has_quotes: false
source: HermesForge Strategies
---
# STR-J Phase 1A Results (Baseline)

## Variants Tested

| Variant | Sig/Yr | Avg R | Win% | Sub-periods | Status |
|---------|--------|-------|------|-------------|--------|
| Baseline (bidirectional) | 3,488 | 0.017 | 32.8% | 2/3 | KILL |
| V1: Long-only | 1,046 | 0.222 | 41.1% | 3/3 | WATCH |
| V2: Short-only | 2,442 | -0.071 | 29.3% | — | KILL |
| V3: tighter threshold | 632 | 0.032 | 33.7% | — | KILL |
| V5: Long + tighter | 148 | 0.210 | 42.7% | 2/3 | KILL |

## Key Finding

Long-only rescue: baseline was KILL at +0.017 avg R, but removing shorts lifts it to +0.222 (WATCH). Shorts structurally negative (avg R -0.071, 29.3% win rate).

## Related
- [[STR-20260726-eufearia-cci-reversal|STR-J Strategy]]
- [[STR-J-phase1b2-stocks]]
- [[FAIL-STR-E-rsi-mean-reversion]]
- [[REGIME-ranging]]
