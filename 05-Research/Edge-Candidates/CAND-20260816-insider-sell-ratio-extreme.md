---
status: staged
source: web
edge_type: insider_sell_ratio_extreme
composite_score: 55.0
confidence: medium
regime_fit: ['complacent', 'caution']
created: 20260816
topic: research
has_quotes: false
tags: [insider-trading, sentiment, external]
---
# Edge Candidate: Insider Buy/Sell Ratio Extreme Low (0.27)

## Source
Web research — GuruFocus Insider Tracker (Aug 2026), InsiderScreener.com, OpenInsider

## Signal
- Overall Market Insider Buy/Sell ratio: 0.27 (as of August 2026)
- This means for every 1 insider buying, ~3.7 are selling
- Historical context: ratio below 0.30 is in the bottom 10th percentile
- Typically associated with market tops or extended valuations
- S&P 500 at record highs (7,790), VIX at 14.25 (complacent)

## Hypothesis
When the aggregate insider buy/sell ratio drops below 0.30:
1. Insiders (who have material non-public information) are collectively signaling that their stocks are overvalued at current levels
2. Historically, ratios below 0.30 have preceded 3-6 month equity drawdowns of 5-10%
3. The signal is most powerful when combined with other complacency indicators (low VIX, high F&G)
4. This is a slow-moving signal — best used as a regime warning, not a timing signal

The current 0.27 ratio combined with VIX at 14.25 and F&G at 62 (Greed) creates a triple-complacency signal.

## Entry Rules
- **As a hedge/regime filter:** Reduce equity exposure by 20-30% when insider B/S ratio < 0.30 AND VIX < 16 AND F&G > 55
- **As a short signal:** Screen for stocks with the highest insider selling (by $ value) in the last 30 days. Short the top 5 on first bearish technical signal (break of 20MA with volume).
- **As a timing filter:** Do not initiate new long swing trades when insider B/S < 0.30 unless the setup is exceptional (A+ grade only)

## Exit Rules
- **Hedge:** Maintain reduced exposure until insider B/S ratio rises above 0.40 or market drops 5%+
- **Short:** Cover on 2R profit or when B/S ratio normalizes above 0.35
- **Filter:** Resume normal operations when B/S > 0.35 or VIX spikes above 22

## Score Breakdown
- Composite: 55.0
- Signal Strength: 10.0 (0.27 is extreme, bottom 10th percentile)
- Confidence: medium (15 pts) — insider selling signals are documented but noisy
- Data Quality: 10 (cached — aggregate ratio from GuruFocus, individual filings from SEC)
- Actionable: 10 (best as regime filter, not direct trade signal)
- Precedent: 10 (well_known — insider trading signals are extensively researched)

## Regime Fit
['complacent', 'caution'] — most relevant when market sentiment is elevated

## Testability
⚠️ Partially testable: Individual SEC Form 4 filings are free from SEC EDGAR. Aggregate B/S ratio is from GuruFocus (free with delay). Can backtest by tracking aggregate insider selling levels vs 3-6 month forward S&P returns. Limited by data availability for historical aggregate ratios.

## Overlap with Engine
Engine scans for insider trading clusters (SEC Form 4 buying patterns) but focuses on BUYING clusters as bullish signals. This is the INVERSE — using aggregate selling as a bearish regime warning. Complementary but opposite direction.

## Recommended Pipeline Action
PROMISING — proceed to backtest as a regime filter overlay. Test: when 30-day aggregate insider B/S ratio < 0.30, does reducing position sizing by 25% improve risk-adjusted returns? The regime filter application is more robust than trying to time shorts.
