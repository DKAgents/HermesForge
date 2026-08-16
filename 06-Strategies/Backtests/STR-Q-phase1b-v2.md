---
title: "STR-Q Phase 1B v2 — Deep Walk-Forward Validation"
strategy: STR-Q
phase: "1B v2"
data_source: "STR-Q-stocks-deep-phase1a.csv"
total_trades: 826
date_range: "2025-08-13 to 2026-08-14"
split_method: "chronological 60/40 (IS/OOS)"
validation_date: "2026-08-15"
status: complete
topic: strategies
confidence: high
has_quotes: false
tags: []
source: HermesForge Strategies
---
# STR-Q Phase 1B v2 — Deep Walk-Forward Validation

## Overview

Deep walk-forward validation of the STR-Q strategy across **826 trades** spanning
**2025-08-13** to **2026-08-14** (1 full year of 5-minute bars).

The trade ledger was sorted chronologically by entry date and split into:

| Segment | Trades | Date Range | Share |
|---------|--------|------------|-------|
| IS (In-Sample) | 495 | 2025-08-13 → 2026-03-18 | 60% |
| OOS (Out-of-Sample) | 331 | 2026-03-18 → 2026-08-14 | 40% |

This is a true walk-forward split — no re-optimization is performed on the OOS segment.

## Headline Metrics

| Metric | IS (60%) | OOS (40%) | Full | Degradation (OOS vs IS) |
|--------|----------|-----------|------|-------------------------|
| Trades | 495 | 331 | 826 | — |
| Win Rate | 45.9% | 46.8% | 46.2% | +2.1% |
| Avg R | 0.5561 | 0.6345 | 0.5875 | +14.1% |
| Median R | -0.5810 | -0.2800 | -0.4415 | — |
| Std R | 1.7710 | 1.7914 | 1.7786 | — |
| Profit Factor | 2.0937 | 2.3102 | 2.1779 | +10.3% |
| Gross Profit (R) | 526.98 | 370.29 | 897.27 | — |
| Gross Loss (R) | 251.70 | 160.29 | 411.99 | — |
| Expectancy (R/trade) | 0.5561 | 0.6345 | 0.5875 | — |
| Max R | 3.00 | 3.00 | 3.00 | — |
| Min R | -1.00 | -1.00 | -1.00 | — |

## Statistical Significance

### One-sample t-test (OOS R-multiples vs 0)

Tests whether the OOS sample mean R-multiple is statistically distinguishable from zero
(i.e., whether the strategy has a real edge on unseen data).

| Statistic | Value |
|-----------|-------|
| Sample size (n) | 331 |
| Mean R | 0.6345 |
| Std R | 1.7914 |
| Std Error | 0.0985 |
| t-statistic | 6.4433 |
| p-value (two-tailed) | 0.000000 |
| 95% CI for mean R | [0.4407, 0.8282] |
| Significant at α=0.05? | **YES** |
| Significant at α=0.01? | **YES** |

### Two-sample Welch's t-test (IS vs OOS)

Tests whether the IS and OOS segments have statistically different mean R-multiples
(a regime-change / overfitting indicator).

| Statistic | Value |
|-----------|-------|
| t-statistic | -0.6187 |
| p-value (two-tailed) | 0.536333 |
| Significant difference? | NO |

:::tip PASS
The OOS segment retains a statistically significant positive edge (p < 0.05),
and IS vs OOS means are not significantly different — no evidence of overfitting.
:::

## Monthly Breakdown

| month   |   trades |   win_rate |   avg_r |   total_r |
|:--------|---------:|-----------:|--------:|----------:|
| 2025-08 |       39 |      0.410 |   0.405 |    15.779 |
| 2025-09 |       70 |      0.514 |   0.637 |    44.567 |
| 2025-10 |       83 |      0.434 |   0.468 |    38.843 |
| 2025-11 |       61 |      0.492 |   0.629 |    38.351 |
| 2025-12 |       75 |      0.413 |   0.265 |    19.894 |
| 2026-01 |       62 |      0.419 |   0.539 |    33.421 |
| 2026-02 |       57 |      0.561 |   1.001 |    57.046 |
| 2026-03 |       72 |      0.444 |   0.685 |    49.319 |
| 2026-04 |       65 |      0.446 |   0.556 |    36.133 |
| 2026-05 |       68 |      0.544 |   0.960 |    65.248 |
| 2026-06 |       63 |      0.444 |   0.650 |    40.974 |
| 2026-07 |       87 |      0.483 |   0.511 |    44.422 |
| 2026-08 |       24 |      0.292 |   0.053 |     1.283 |

## OOS Per-Symbol Breakdown

| symbol   |   trades |   win_rate |   avg_r |   total_r |
|:---------|---------:|-----------:|--------:|----------:|
| AAPL     |       49 |      0.612 |   1.112 |    54.509 |
| TSLA     |       44 |      0.568 |   0.932 |    41.028 |
| GOOGL    |       39 |      0.487 |   0.786 |    30.639 |
| SPY      |       34 |      0.559 |   0.726 |    24.691 |
| AMZN     |       41 |      0.439 |   0.521 |    21.373 |
| MSFT     |       40 |      0.350 |   0.468 |    18.713 |
| META     |       44 |      0.386 |   0.306 |    13.480 |
| NVDA     |       40 |      0.325 |   0.139 |     5.570 |

## OOS Exit-Type Breakdown

| exit_type   |   trades |   avg_r |   total_r |
|:------------|---------:|--------:|----------:|
| stop        |      153 |  -1.000 |  -153.000 |
| target      |      105 |   3.000 |   315.000 |
| time        |       73 |   0.658 |    48.003 |

## Interpretation

- **Edge persistence:** The OOS avg R of 0.6345 vs IS avg R of 0.5561
  represents a +14.1% shift. Reasonable stability.
- **Win-rate stability:** +2.1% shift IS→OOS.
- **Profit factor:** OOS PF 2.31 vs IS PF 2.09.
- **Statistical verdict:** OOS mean R is statistically significant
  at α=0.05 (p=0.0000). IS/OOS do not differ significantly
  (p=0.5363).

## Verdict

| Check | Result |
|-------|--------|
| OOS positive expectancy | PASS |
| OOS profit factor > 1.0 | PASS |
| OOS edge statistically significant (p<0.05) | PASS |
| IS/OOS mean R not significantly different | PASS |
| Win-rate degradation < 10pp | PASS |
| Avg R degradation < 25% | PASS |

**Overall: PASS**

---

*Generated by `phase1b_v2_walkforward.py`. Do not edit by hand.*
