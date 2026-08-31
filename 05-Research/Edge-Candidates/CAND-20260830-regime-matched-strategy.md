---
status: staged
source: strategy_regime
edge_type: regime_matched_strategy
composite_score: 66.8
confidence: medium
regime_fit: ['risk_on']
created: 20260830
---

# Edge Candidate: STR-Q-liquidity-sweep performs well in risk_on regime

## Source
strategy_regime scanner

## Signal
208 trades, WR=59.1%, avg=+0.99R

## Hypothesis
Based on 208 historical trades, STR-Q-liquidity-sweep has a positive edge in risk_on conditions. Increase scanning frequency for this strategy.

## Entry Rules
Prioritize STR-Q-liquidity-sweep signals. Increase position size by 50% (from 1% to 1.5% risk) when regime matches.

## Exit Rules
Follow strategy's standard exit rules.

## Score Breakdown
- Composite: 66.8
- Signal Strength: 14.8
- Confidence: medium (15 pts)
- Data Quality: 15
- Actionable: 15
- Precedent: 7

## Regime Fit
['risk_on']

## Recommended Pipeline Action
SPECULATIVE — quick Phase 1A backtest to check for edge.
