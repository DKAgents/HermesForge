---
status: backtest_failed
pipeline_notes: Phase 1A: mean_r=-0.311 (p=0.0, t=-12.813), 5775 signals. NEGATIVE mean R — failed. Breadth divergence as coded shows no positive edge. Divergence timing signal not captured correctly by exit simulation.
source: breadth
edge_type: breadth_divergence
composite_score: 69.2
confidence: medium
regime_fit: ['risk_on', 'caution']
created: 20261001
---

# Edge Candidate: BEARISH divergence: price moving one way, breadth the other

## Source
breadth scanner

## Signal
A/D ratio=1.01, 26.3% above 50MA, 45.6% above 200MA

## Hypothesis
Breadth divergences often precede reversals. If bearish divergence: consider reducing longs or entering shorts. If bullish divergence: look for bottoming setups.

## Entry Rules
Wait for price confirmation in divergence direction. Entry on first close in divergence direction with volume > 20d avg.

## Exit Rules
Exit when breadth re-aligns with price or after 10 bars.

## Score Breakdown
- Composite: 69.2
- Signal Strength: 14.2
- Confidence: medium (15 pts)
- Data Quality: 15
- Actionable: 15
- Precedent: 10

## Regime Fit
['risk_on', 'caution']

## Recommended Pipeline Action
SPECULATIVE — quick Phase 1A backtest to check for edge.
