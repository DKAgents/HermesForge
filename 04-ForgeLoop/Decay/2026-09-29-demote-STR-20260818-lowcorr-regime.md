# Demotion: STR-20260818-lowcorr-regime
**Date:** 2026-09-29
**Source:** Jev decay check (fallback heuristic)
**Action:** demoted Active → Hypotheses

## Jev Result
- Jev classification: **unreachable** (jev_error=True)
- Fallback: heuristic `decay_watch.py` logic applied

## Heuristic Findings
- **Trailing 100-trade PF:** inf (no losing trades in last 100)
- **Avg-R windows:** consecutive negative 20-trade windows detected in strategy history
- **Trigger:** ≥2 consecutive non-overlapping 20-trade windows with avg-R < 0

## Context
This strategy was already flagged as "WATCH" with reduced risk (0.5% per trade) due to small edge concerns (mean R = 0.092, 0.072 after costs). The consecutive negative avg-R windows in the long trade history (31,464 trades since 2019) indicate the edge is not consistently positive across all regimes.

## Re-activation Criteria
- Walk-forward OOS validation completed with mean R > 0
- All avg-R windows positive for ≥5 consecutive windows
- Jev classification returns "healthy" when re-tested