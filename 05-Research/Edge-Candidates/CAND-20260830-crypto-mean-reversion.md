---
status: backtest_failed
source: rotation
edge_type: crypto_mean_reversion
composite_score: 72.3
confidence: medium
regime_fit: ['neutral', 'risk_on']
created: 20260830
processed: 20260831
notes: BACKTEST_FAILED — Phase 1A: 1 signal only, mean R=+1.122, p_value=1.0, sig/yr < 12 → KILL. OP daily data limited on Hyperliquid; RSI<35 + close-near-20MA condition extremely selective. Single-asset mean reversion lacks signal frequency to survive ADR-004 thresholds. Reconsider with broader crypto universe or higher timeframe.
---

# Edge Candidate: OP down -20.3% in 7d but up 5.1% in 30d

## Source
rotation scanner

## Signal
7d: -20.3%, 30d: +5.1%

## Hypothesis
Short-term oversold in uptrend. Buy OP for mean reversion bounce. Typical recovery: 30-50% of the 7d drop within 3-5 days.

## Entry Rules
Buy OP when daily RSI < 35 AND price near 20MA. Stop below recent swing low.

## Exit Rules
Exit at 50% of 7d drop recovery, or RSI > 60, or 5 bars.

## Score Breakdown
- Composite: 72.3
- Signal Strength: 20.3
- Confidence: medium (15 pts)
- Data Quality: 15
- Actionable: 15
- Precedent: 7

## Regime Fit
['neutral', 'risk_on']

## Recommended Pipeline Action
SPECULATIVE — quick Phase 1A backtest to check for edge.
