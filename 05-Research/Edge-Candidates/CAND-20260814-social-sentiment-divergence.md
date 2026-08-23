---
status: rejected
source: sentiment
edge_type: social_sentiment_divergence
composite_score: 48.6
confidence: low
regime_fit: ['caution', 'complacent']
created: 20260814
topic: research
has_quotes: false
tags: []
---
# Edge Candidate: BNB: sentiment 86 but price trend DOWN

## Source
sentiment scanner

## Signal
Sentiment: 86, Trend: down, Galaxy: 63

## Hypothesis
Social sentiment for BNB is very high (86) but price is trending down. This divergence suggests smart money is distributing to retail. Bearish signal.

## Entry Rules
Short BNB on next bounce to 10MA. Stop above recent high. Small size (0.25% risk).

## Exit Rules
Exit at -10% or when sentiment drops below 40.

## Score Breakdown
- Composite: 48.6
- Signal Strength: 8.6
- Confidence: low (5 pts)
- Data Quality: 15
- Actionable: 15
- Precedent: 5

## Regime Fit
['caution', 'complacent']

## Recommended Pipeline Action
SPECULATIVE — quick Phase 1A backtest to check for edge.

## Pipeline Rejection (2026-08-23)
**Decision:** REJECT at Stage 1 (Read & Critique)

**Rationale:** The hypothesis requires social sentiment data (e.g., LunarCrush, Santiment,
or similar sentiment API) to measure the divergence between sentiment score and price trend.

**Issues:**
- Our data pipeline provides OHLCV only (yfinance for 529 stocks, Hyperliquid for 35 crypto)
- No social sentiment data feed is integrated
- Cannot test "sentiment 86 but price trending down" without sentiment time series
- The engine's `sentiment` module may exist but is not part of the Phase 1A backtest pipeline

**Recommendation:** If social sentiment data becomes available (e.g., via X API, LunarCrush,
or Santiment integration), this candidate can be re-staged. The hypothesis is well-formed
and testable — it just needs the data feed.

## Related
- [[N118-hpi-divergence-analysis-warning-of-trend-change]] — See technical-analysis-financial-markets-murphy/patterns/N118-hpi-divergence-analysis-warning-of-trend-change for divergence analysis foundation
