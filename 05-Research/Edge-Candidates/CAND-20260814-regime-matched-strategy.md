---
status: rejected
source: strategy_regime
edge_type: regime_matched_strategy
composite_score: 49.5
confidence: low
regime_fit: ['caution']
created: 20260814
topic: research
has_quotes: false
tags: []
---
# Edge Candidate: STR-P-crosssectional performs well in caution regime

## Source
strategy_regime scanner

## Signal
4 trades, WR=50.0%, avg=+0.50R

## Hypothesis
Based on 4 historical trades, STR-P-crosssectional has a positive edge in caution conditions. Increase scanning frequency for this strategy.

## Entry Rules
Prioritize STR-P-crosssectional signals. Increase position size by 50% (from 1% to 1.5% risk) when regime matches.

## Exit Rules
Follow strategy's standard exit rules.

## Score Breakdown
- Composite: 49.5
- Signal Strength: 7.5
- Confidence: low (5 pts)
- Data Quality: 15
- Actionable: 15
- Precedent: 7

## Regime Fit
['caution']

## Recommended Pipeline Action
SPECULATIVE — quick Phase 1A backtest to check for edge.

## Pipeline Rejection (2026-08-23)
**Decision:** REJECT at Stage 1 (Read & Critique)

**Rationale:** This is not a standalone edge candidate. STR-P-crosssectional already exists
as `scanner_p_crosssectional.py` and is registered in the regime-strategy map. This candidate
proposes a position-sizing overlay (1.5x risk when regime = "caution"), not a new scanner.

**Issues:**
- The regime term "caution" does not match our regime detector's output vocabulary
  (trending/ranging/transitional/high-volatility/low-volatility)
- STR-P is already mapped to ["ranging", "trending"] in STRATEGY_REGIME_MAP
- Position-sizing adjustments belong in `regime_strategy_selector.py`, not as a new scanner
- No new signal logic to code or backtest

**Recommendation:** Close this candidate. If regime-based position sizing for STR-P is desired,
implement it directly in `scripts/data/regime_strategy_selector.py` as a risk_multiplier
adjustment.
