---
status: rejected
source: web
edge_type: macro_event_volatility_regime
rejection_reason: Event-specific and non-backtestable as a scanner. Jackson Hole occurs once/year; cannot generate sufficient signal count for Phase 1A statistical testing (minimum 12 sigs/yr). Event is 2 days away — manual risk-reduction overlay already recommended.
composite_score: 65.0
confidence: medium
regime_fit: ['neutral', 'caution', 'complacent']
created: 20260823
topic: research
has_quotes: true
tags: [macro, event-driven, jackson-hole, fed, volatility, regime-shift]
---

# Edge Candidate: Jackson Hole Fed Regime-Shift Volatility Event

## Source
Web / macro research (Aug 17-22, 2026):
- **Jackson Hole Symposium (Aug 27-29, 2026):** Fed Chair Kevin Warsh expected to unveil a new monetary framework or "put more flesh on a Federal policy pivot" — described as the "next obvious monetary-policy waypoint" (Investing.com, Aug 17 2026, 6 days ago).
- **Convera FX Research (Aug 21 2026):** "US Treasury buybacks briefly eased bond-market stress, but rising debt concerns, dollar weakness and Jackson Hole remain key market risks." A "renewed credibility problem" for the Fed.
- **Capital Flows Research (Aug 20 2026):** "How Bessent Is Establishing A New Monetary Order" — Treasury Secretary Bessent's regulatory shifts are changing capital flows and macro liquidity dynamics, setting the stage for a regime announcement at Jackson Hole.
- **BofA's Hartnett (Aug 21 2026):** Warns of dollar slump + risk selloff if bond intervention fails — directly relevant as Jackson Hole could address Treasury market stability.
- **Context:** The macro backdrop entering Jackson Hole is extreme bullish positioning (BofA Bull & Bear 9.5), S&P 500 at record highs, VIX near 2026 lows (~15-16), and rising US debt/dollar concerns. Any hawkish surprise or lack of clarity from Warsh could trigger a sharp repricing.

## Signal
A **scheduled macro event with elevated regime-shift probability.** Unlike earnings or economic data events, Jackson Hole has historically produced multi-month regime shifts because it represents forward guidance on the entire monetary policy path. The current setup combines:
1. **Extreme complacency:** VIX at 2026 lows, SPX at ATH, BofA Bull & Bear at 9.5
2. **Elevated uncertainty:** New Fed Chair (Warsh), new Treasury Secretary (Bessent), "new monetary order" narrative
3. **Asymmetric payoff:** The market has priced in a dovish/status-quo outcome; any hawkish surprise or framework change could trigger a 3-5%+ SPX move and a 10-20+ point VIX spike

The edge is NOT directional — it's a **volatility-regime** edge: reduce net exposure before the event and position for a volatility spike, then re-enter after the new regime is priced.

## Entry Rules
- **Pre-event (T-3 days: Aug 24-26):** Reduce all LIVE stock strategy risk_multipliers by 30-50%. Close any marginal or sub-breakeven positions. Raise cash.
- **Event day (Aug 27-29):** Do not initiate new positions. If the regime selector already has a reduced-risk posture, maintain it.
- **Post-event re-entry (Aug 30+):**
  - IF the speech is dovish/neutral AND SPX rallies + VIX stays below 18 → restore full allocations, bias toward breakout + trend-following strategies
  - IF the speech is hawkish/surprise AND SPX drops 2%+ with VIX spike → stay defensive for 5-10 trading days, focus on mean-reversion strategies (STR-Z, STR-AA, STR-AC) which work well after vol spikes
  - IF ambiguous/no clear signal → restore 50% allocation, wait 3 days for clarity

## Exit Rules
- The event edge expires after T+10 trading days (Sep 11, 2026). By then, the new regime should be fully priced.
- If no regime shift materializes (SPX within ±2%, VIX < 20 through Sep 11), restore all strategies to full allocation.

## Score Breakdown
- Composite: 65.0
- Signal Strength: 18.0 (Jackson Hole is a real, scheduled, high-impact event; multiple sources confirm the regime-shift narrative; the complacency backdrop amplifies the signal)
- Confidence: medium (15) — Jackson Hole has historically moved markets, but not every year; Warsh's first symposium as Chair adds uncertainty; the direction of the move is unknowable, only the volatility setup
- Data Quality: 15 (event date is known; VIX, SPX, and sector ETFs are daily via yfinance; no external data feeds needed for post-event monitoring)
- Actionable: 12 (risk-reduction overlay is straightforward to implement; re-entry rules are clear and conditional on observable outcomes)
- Precedent: 5 (some_evidence — Jackson Hole 2010 (QE2), 2014 (labor market shift), 2022 (hawkish Powell) all produced multi-month regime shifts; not a deeply-replicated academic anomaly but a well-known macro event pattern)

## Regime Fit
['neutral', 'caution', 'complacent'] — This edge is most impactful when the pre-event regime is complacent (VIX low, SPX high, positioning extreme) because the surprise potential is largest. In risk_off (already defensive) the edge has minimal marginal value. In aggressive risk_on it still applies (reduce risk ahead of a binary event).

## Testability
⚠️ **Not backtestable in the traditional sense** — Jackson Hole events are rare (once/year) and regime-shifts are qualitative. However, the edge can be validated by:
1. **Historical event study:** For each Jackson Hole since 2010, measure the SPX 2-week forward return distribution conditional on pre-event VIX level. If pre-event VIX < 18, forward vol is higher (VIX spikes 5+ points within 2 weeks in X of Y cases).
2. **Generic macro-event template:** This edge can be templated for future FOMC decisions, CPI releases, and other high-impact scheduled events with extreme pre-event complacency.
3. **Paper-trading validation:** Apply the risk-reduction overlay THIS WEEK (Aug 24-29) and measure actual P&L impact vs. a no-overlay baseline. This is a live forward-test.

**Overlap with engine:** Engine does NOT currently account for scheduled macro events in its strategy risk adjustments. The regime_strategy_selector mentions "economic event proximity" as a filter condition but does not have explicit Jackson Hole / FOMC event logic. This edge fills that gap.

## Recommended Pipeline Action
**PROMISING →** This is a time-critical edge:
1. **Immediate (Aug 24):** Apply a 50% risk_multiplier reduction to all LIVE stock strategies for 1 week (Aug 24-29). This is conservative and reversible.
2. **Post-event (Aug 30):** Assess the speech outcome and apply the re-entry rules above.
3. **Template creation:** Build a generic `macro_event_risk_overlay.py` that accepts event date, confidence level, and pre/post rules — reusable for future FOMC/CPI/Jackson Hole events.
4. Priority: CRITICAL — the event is 4 days away and the market is at extremes. The overlay should be applied immediately.