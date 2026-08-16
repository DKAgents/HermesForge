---
type: user-story
story: US-110
epic: EPIC-013
title: "Walk-Forward Validation of Stop Optimization"
status: Done
created: 2026-08-15
completed: 2026-08-15
tags: [validation, walk-forward, stop-optimization, str-q]
---

# US-110: Walk-Forward Validation of Stop Optimization

## Summary

Validated the US-109 per-level-type stop optimization via proper walk-forward testing. Result: **CURVE-FIT** — the optimization did not generalize to out-of-sample data. Reverted to 1.0R stops for all level types.

## Methodology

1. Re-ran 696-trade deep backtest with full MAE/MFE tracking
2. Split by time into IS (417 trades, 60%) and OOS (279 trades, 40%)
3. Grid-searched optimal stop caps on IS data only
4. Applied IS-optimal caps to OOS and measured improvement
5. Bootstrap significance test (1000 iterations)

## Results

| Metric | IS Baseline | IS Optimized | OOS Baseline | OOS Optimized |
|--------|------------|-------------|-------------|-------------|
| Avg R | +0.712 | +0.762 | +0.953 | +0.894 |
| Improvement | — | +0.050R | — | **-0.059R** |
| p-value | — | — | — | **0.928** |

**Verdict: CURVE-FIT.** The IS improvement (+0.050R) reversed sign in OOS (-0.059R). The optimization found noise, not signal. Overfit ratio: -0.85x.

## Action Taken

Reverted `STOP_RISK_CAP` in `detect_liquidity_sweeps.py` to empty dict (all 1.0R). The original wick-based stop is optimal.

## Key Lesson

The US-109 stop optimization looked brilliant in-sample (+35% expectancy) but was pure overfitting. This is exactly why walk-forward validation is non-negotiable. Without US-110, we would have deployed an inferior stop system to live trading.