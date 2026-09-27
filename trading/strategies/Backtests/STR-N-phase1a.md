---
type: backtest-result
strategy_id: STR-20260726-outside-day-key-reversal
strategy_name: STR-N Outside Day Key Reversal
phase: 1A
verdict: KILL
date: 2026-07-26
metrics:
  total_signals: 28
  signals_per_year: 4.2
  avg_r: -0.037
  win_rate: 46.4
  sub_periods_positive: 1
  sub_periods:
    period1_bull: -0.516
    period2_bear: -0.277
    period3_current: +0.332
  exit_breakdown:
    time: 15
    stop: 13
    target: 0
data_limitations: "Daily bars, survivorship bias, 529-ticker universe"
tags: [backtest-result, phase1a, killed, outside-day, reversal]
topic: strategies
confidence: high
has_quotes: false
source: HermesForge Strategies
---
# Backtest Result: STR-N Phase 1A

## Summary

| Metric | Value |
|--------|-------|
| Total signals | 28 |
| Signals/year | 4.2 |
| Average R | -0.037 |
| Win rate | 46.4% |
| Sub-periods positive | 1/3 (period3_current only) |
| Target hits | 0 (0%) |
| Time stops | 15 (53.6%) |
| Stop hits | 13 (46.4%) |
| Classification | ❌ KILL |

## Phase 1B Perturbation Results

| Variant | Sigs | Avg R | Win% | SP+ | Notes |
|---------|------|-------|------|-----|-------|
| V1: Baseline (12-bar, 3:1) | 25 | -0.065 | 44.0% | 1/3 | period3: +0.326 |
| V2: Longer time stop (20 bars) | 25 | +0.110 | 52.0% | 1/3 | period3: +0.620 |
| V3: Lower target (2:1) + 20-bar | 25 | +0.004 | 52.0% | 1/3 | Lowering target hurt |
| V4: Stricter vol (2x) + 2:1 + 20 | 6 | -1.000 | 0.0% | 0/3 | Too restrictive |
| V5: 3-day decline + 2:1 + 20 | 15 | +0.125 | 60.0% | 1/3 | period3: +0.574 |
| V6: Vol 2x + 3-day + 2:1 + 20 | 3 | -1.000 | 0.0% | 0/3 | Too restrictive |

## Analysis

1. **Time stop is the key lever** — extending from 12→20 bars lifts avg R from -0.065 to +0.110
2. **Target reduction hurts** — lowering to 2:1 doesn't help (V3 vs V2)
3. **3-day decline helps win rate** — V5 gets 60% win rate but fewer signals
4. **Period3_current edge is strong** — +0.620 avg R (V2), +0.574 (V5)
5. **Period1_bull is the drag** — consistently negative across all variants (-0.375 to -0.687)

## Failure Analysis (Overall)

The strategy has a **regime-dependent edge** that only manifests in the 2024+ period (period3_current). In the 2019-2021 bull market and 2022-2023 bear market, the outside day reversal after decline fails — the reversal is false and price continues lower. In the 2024+ period, the reversal works, possibly due to different market structure or higher retail participation.

Overall avg R (+0.125 best variant V5) is below the 0.2 kill threshold. However, the period3_current edge (+0.574) is significant and worth monitoring as a potential future research lead if the regime persists.

## Future Research Path

If the 2024+ regime persists (elevated volatility, AI-driven rotation), the outside day key reversal may become viable. A regime-gated version that only activates in "current regime" conditions could be tested in Phase 1B/2. This is deferred until we have more period3 data to confirm the edge is structural rather than a small-sample artifact.

## Related

- [[STR-20260726-outside-day-key-reversal|STR-N Strategy]]
- [[REGIME-high-volatility]]
- [[Discoveries-2026-W32-high-vol]]
- [[ADR-004-Phase1-Validation-Framework]]