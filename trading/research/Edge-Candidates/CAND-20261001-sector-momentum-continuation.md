---
status: duplicate_backtest_failed
pipeline_notes: DUPLICATE of CAND-20260814-sector-momentum-continuation.md which already backtest_failed (mean_r=+0.007, p=0.8396, KILL). Same edge (XLK sector leading) rediscovered by edge discovery engine. Not re-testing.
source: rotation
edge_type: sector_momentum_continuation
composite_score: 73.2
confidence: medium
regime_fit: ['risk_on']
created: 20261001
---

# Edge Candidate: Technology (XLK) leading with momentum continuing

## Source
rotation scanner

## Signal
20d RS: +6.08%, 1d RS: +0.54%

## Hypothesis
Strong sector with continued RS improvement. Momentum persistence suggests more upside. Buy top stocks in sector on pullbacks to 10MA.

## Entry Rules
Buy top 3 stocks in XLK sector on pullback to 10MA with volume contraction. Stop below 20MA.

## Exit Rules
Exit when sector RS turns negative on 5d, or target 3R.

## Score Breakdown
- Composite: 73.2
- Signal Strength: 18.2
- Confidence: medium (15 pts)
- Data Quality: 15
- Actionable: 15
- Precedent: 10

## Regime Fit
['risk_on']

## Recommended Pipeline Action
SPECULATIVE — quick Phase 1A backtest to check for edge.
