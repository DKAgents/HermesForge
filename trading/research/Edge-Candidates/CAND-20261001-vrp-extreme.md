---
status: pipeline_hold
pipeline_notes: Phase 1A PASS: mean_r=+0.107 (p=0.0, t=5.907), 3621 signals, 52.7% WR. Statistically significant edge. But mean_r < 0.2 (friction flag) and walk-forward registration (adding STRATEGY_CONFIGS entry to walk_forward.py + deploy) deferred — requires STRATEGY_CONFIGS entry to proceed to walk-forward. Scanner: scanner_vrp_extreme.py. Related to existing STR-20260816-VIX-VRP-CONTANGO (mean_r=+0.093, same direction). This VRP-threshold variation is a slightly different trigger.
source: volatility
edge_type: vrp_extreme
composite_score: 72.7
confidence: medium
regime_fit: ['risk_off']
created: 20261001
topic: general
has_quotes: false
tags: []
---
# Edge Candidate: Volatility risk premium extreme: +5.9% (VIX overestimating fear)

## Source
volatility scanner

## Signal
VIX=16.83, Realized=10.94%

## Hypothesis
Large positive VRP → market pricing in too much fear, likely to resolve with VIX compression (bullish). Large negative VRP → market too complacent, spike risk elevated.

## Entry Rules
If VRP > +3%: buy stocks breaking out (VIX should compress). If VRP < -3%: reduce longs, add hedge.

## Exit Rules
Exit when VRP returns to ±1% range.

## Score Breakdown
- Composite: 72.7
- Signal Strength: 17.7
- Confidence: medium (15 pts)
- Data Quality: 15
- Actionable: 15
- Precedent: 10

## Regime Fit
['risk_off']

## Recommended Pipeline Action
SPECULATIVE — quick Phase 1A backtest to check for edge.
