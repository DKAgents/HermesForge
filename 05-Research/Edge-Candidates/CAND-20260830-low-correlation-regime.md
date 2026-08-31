---
status: staged
source: correlation
edge_type: low_correlation_regime
composite_score: 73.1
confidence: high
regime_fit: ['risk_on', 'neutral']
created: 20260830
---

# Edge Candidate: Diversified market: avg correlation 0.22 (stock-picking environment)

## Source
correlation scanner

## Signal
Avg 30d correlation = 0.219

## Hypothesis
Low correlation = individual stock edge matters. Best time for stock-specific strategies (STR-A, STR-B, STR-I). Sector rotation and factor strategies work well here.

## Entry Rules
Run stock-picking scanners (MACD divergence, adaptive trend, pullback to MA). Focus on stocks with idiosyncratic catalysts.

## Exit Rules
Continue until correlation rises above 0.5.

## Score Breakdown
- Composite: 73.1
- Signal Strength: 8.1
- Confidence: high (25 pts)
- Data Quality: 15
- Actionable: 15
- Precedent: 10

## Regime Fit
['risk_on', 'neutral']

## Recommended Pipeline Action
PROMISING — proceed to full backtest and walk-forward validation.
