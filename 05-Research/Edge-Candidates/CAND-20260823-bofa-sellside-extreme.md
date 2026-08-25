---
status: rejected
source: web
edge_type: macro_sentiment_composite_extreme
rejection_reason: Regime overlay, not a per-ticker scanner. BofA Bull & Bear indicator is proprietary. The proposed proxy (F&G + P/C + Breadth + VIX) is a risk-management overlay for existing strategies, not a standalone signal generator. Defer to risk-management module enhancement task.
composite_score: 76.0
confidence: high
regime_fit: ['complacent', 'risk_on', 'caution']
created: 20260823
topic: research
has_quotes: true
tags: [macro, sentiment-extreme, sell-side, contrarian, institutional]
---

# Edge Candidate: BofA Composite Sentiment Extreme (SELL Territory)

## Source
Web / institutional research (Aug 21-22, 2026):
- **BofA Bull & Bear Indicator climbed to 9.5 from 9.3** — deep in "SELL" territory, driven by stronger global stock breadth and bullish positioning in equities (Investing.com, Aug 21 2026, 2 days ago). The indicator has a strong historical track record (13-of-15 prior sell signals correctly flagged downturns).
- **BofA Global Fund Manager Survey (mid-Aug 2026):** "One of the most bullish readings of investor sentiment" — cash allocations low, equity allocations high, risk appetite elevated (Canadian Mining Report, Aug 19 2026, 4 days ago).
- **BofA's Hartnett** sees dollar slump + risk selloff if Treasury bond intervention fails (Investing.com, Aug 21 2026).
- **S&P 500 at record highs ~7,790** as of Aug 5, driven by strong earnings and AI optimism (Reuters, Aug 5 2026).
- **Convera FX Research (Aug 21 2026):** US Treasury buybacks briefly eased bond-market stress, but rising debt concerns, dollar weakness, and Jackson Hole remain key market risks.

## Signal
A **multi-indicator sentiment composite at extreme bullish levels** across both retail/institutional positioning and sell-side consensus:

1. **BofA Bull & Bear: 9.5** (scale 0-10, 10 = max bullish/sell signal)
2. **BofA FMS:** Cash levels at multi-year lows; equity OW at extreme
3. **SPX:** At or near all-time highs (~7,790)
4. **Sell-side consensus:** Broadly bullish (J.P. Morgan, Reuters mid-Aug)
5. **VIX:** Near 2026 lows (sub-16), deep contango

This is the mirror-image of extreme fear buying signals — when institutional and retail positioning are simultaneously max-long and the sell-side indicator flashes, the asymmetry of forward returns skews negative. The edge is NOT a timing signal (it can stay extreme for weeks), but a **position-sizing and risk-management trigger**: reduce net long exposure and prepare for mean-reverting drawdown when the composite is above thresholds.

## Hypothesis
When the BofA Bull & Bear Indicator exceeds 7.0 AND SPX is within 2% of its 52-week high AND the VIX is ≤ 16 (complacency floor), forward 1-3 month equity returns have negative skew. Reducing net long exposure by 30-50% and rotating into defensive sectors or cash during this regime improves risk-adjusted returns. The edge compounds when multiple sentiment extremes fire simultaneously (Bull & Bear + FMS cash lows + VIX floor).

## Entry Rules
- **Sentiment Composite Check (weekly, Friday close):** Fire when:
  1. BofA Bull & Bear Indicator ≥ 7.0 (proxy: track via news/investing.com updates; backup: use our own Fear & Greed + Put/Call + Breadth to approximate, but the BofA indicator itself has stronger track record)
  2. SPX within 2% of 52-week high
  3. VIX ≤ 18 (relaxed from 16 since the BofA indicator itself captures the extreme)
- **Action when triggered:** Reduce all LIVE strategy allocations by 50% (risk_multiplier 0.5 overlay). Shift remaining 50% to defensive sector ETFs (XLP, XLU, XLV) or SPY with a 5% trailing stop.
- **No new entries** in breakout or trend-following strategies. Allow only mean-reversion and reversal strategies (which tend to work when extremes reverse).

## Exit Rules
- Exit the defensive overlay when BofA Bull & Bear drops below 5.0 OR SPX corrects ≥ 5% from the trigger price (the edge has been "consumed" by the drawdown) OR VIX spikes above 25.
- Restore full strategy allocations gradually over 2 weeks.

## Score Breakdown
- Composite: 76.0
- Signal Strength: 24.0 (Bull & Bear at 9.5/10 is near-maximum signal; multi-source corroboration from FMS, Hartnett, Convera)
- Confidence: high (20) — BofA indicator has a documented 13-of-15 track record; the sentiment composite is one of the most reliable contrarian signals in macro
- Data Quality: 12 (BofA indicator updates are weekly but public; FMS is monthly but public; VIX and SPX are daily via yfinance)
- Actionable: 12 (risk-overlay on existing strategies — no new single-name trades needed; implementable as a regime-level multiplier)
- Precedent: 8 (well_known — sentiment extremes as contrarian signals are among the most studied behavioral edges; BofA's own indicator is published with backtested performance)

## Regime Fit
['complacent', 'risk_on', 'caution'] — This edge fires specifically when positioning is max-bullish while macro risks (Jackson Hole, dollar, bonds) are brewing. The edge is complementary to the existing rate-hike-complacency candidate (which failed on too-strict gate) but uses a cleaner, more direct sentiment composite.

## Testability
✅ **Partially testable with free data.** The BofA indicator itself is proprietary/requires manual tracking, but the edge can be backtested using our own sentiment composite:
- Our F&G + Put/Call + Breadth (pct above 50MA) + VIX can proxy the "extreme composite"
- Condition: F&G > 70 AND P/C < 0.7 AND Breadth > 70% AND VIX < 18
- Backtest reducing strategy allocations by 50% when this composite fires, vs. running at full allocation
- Measure: drawdown reduction, Sharpe improvement, Calmar ratio

**Overlap with engine:** Engine only covers F&G extremes for crypto and P/C extremes for stocks independently. It does NOT combine them into a composite sentiment extreme for stock strategy risk management. The BofA Bull & Bear is a separate institutional indicator not currently tracked by the engine. Genuinely new edge type for the pipeline.

## Recommended Pipeline Action
**PROMISING →** Build a sentiment-composite risk-overlay module that:
1. Tracks our internal sentiment composite (F&G + P/C + Breadth + VIX) daily
2. When the composite fires, applies a 0.5x risk_multiplier to all LIVE stock strategies
3. Backtest this overlay on the existing strategy portfolio (STR-B, STR-I, STR-Z, etc.) and measure risk-adjusted improvement
4. Separately, set up a web scraper or manual weekly check of the BofA Bull & Bear Indicator as a higher-quality signal (it updates every Tuesday)
5. Priority: HIGH — the signal is active RIGHT NOW (Bull & Bear at 9.5) and may precede a summer/fall correction. Timeliness is critical.