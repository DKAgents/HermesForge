---
type: backtest-result
strategy_id: STR-D
strategy_name: S/R Role Reversal
phase: walk-forward
asset_class: stocks
direction: long-only
universe: 529 tickers (full), 30 (optimization sample)
period_start: 2019-01-01
period_end: 2026-12-31
verdict: KILLED
verdict_reason: "Walk-forward shows NO EDGE (p=0.435, CI includes zero). Phase 1A frictionless edge (0.227R) does not survive transaction costs. OOS R=0.033 with costs, below 0.2 kill threshold. Only tested on stocks — killed globally per ADR-004 Amendment 1."
data_limitations: "Daily bars, survivorship bias, quick mode (1 param combo)"
produced_by: "Walk-Forward Framework"
tags: [backtest, walkforward, STR-D, stocks, killed]
topic: strategies
confidence: high
has_quotes: false
source: HermesForge Strategies
---
# STR-D Walk-Forward Validation Results (Stocks)

## Method
Per-ticker walk-forward validation. 5 rolling windows (2-year train, 1-year test).
Optimization on 30-ticker sample, testing on full 529-ticker universe.
Transaction costs applied: 12bp round-trip (stocks).

## Results

### In-Sample (Full Period, Default Params)
- **2410 signals**, avg R = 0.0572 (with costs)

### Out-of-Sample Per Window

| Window | Train R | Train N | OOS R | OOS N | Win Rate |
|--------|---------|---------|-------|-------|----------|
| 2022   | -0.0654 | 33      | **-0.5208** | 395   | 30%      |
| 2023   | -0.2246 | 46      | **+0.3581** | 458   | 57%      |
| 2024   | +0.1522 | 69      | **+0.2490** | 305   | 51%      |
| 2025   | +0.2959 | 75      | **-0.1149** | 402   | 44%      |
| 2026   | +0.4124 | 64      | **+0.3871** | 181   | 54%      |

### OOS Significance (All Windows Combined)
- **N = 1741 signals**
- **Mean R = 0.0334** (with costs)
- **t-stat = 0.78, p-value = 0.4350**
- **95% CI = [-0.0496, 0.1166]**
- **Verdict: NO EDGE** (CI includes zero, p >> 0.05)

### Per-Window Verdict
- 2022: NO EDGE (strongly negative, 30% win rate)
- 2023: FRAGILE EDGE (positive, 57% win rate)
- 2024: POSSIBLE EDGE (positive, 51% win rate)
- 2025: NO EDGE (negative, 44% win rate)
- 2026: FRAGILE EDGE (positive, 54% win rate)

## Assessment

### Why It Failed
1. **Phase 1A edge doesn't survive costs**: The frictionless avg R of 0.227 (Phase 1A WATCH) drops to 0.057 in-sample and 0.033 OOS after adding 12bp round-trip costs.
2. **Inconsistent across windows**: 2 of 5 windows are strongly negative (2022: -0.52, 2025: -0.11), wiping out the positive windows.
3. **Not statistically significant**: p = 0.435, CI includes zero — cannot reject the null hypothesis of no edge.
4. **Win rate too low for a support/resistance strategy**: 30-44% in losing windows, barely 50-57% in winning windows.

### Comparison to Phase 1A
| Metric | Phase 1A (frictionless) | Walk-Forward (with costs) |
|--------|------------------------|--------------------------|
| Avg R  | 0.227                  | 0.033                    |
| N      | 63/year                | 1741 total               |
| Win Rate | 50.3%                | ~47% average            |

### Verdict: KILLED
Per ADR-004 Amendment 1:
- Walk-forward verdict: NO EDGE (p=0.435, CI includes zero)
- OOS avg R = 0.033 (with costs) — below 0.2 kill threshold (frictionless)
- Only tested on stocks → fails on the only tested asset class → KILLED globally
- The near-miss scanner in the pipeline should be disabled

## Related
- [[STR-D-phase1a]]
- [[ADR-004-Phase1-Validation-Framework]]