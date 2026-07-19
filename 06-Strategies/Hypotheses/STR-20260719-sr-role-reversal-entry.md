---
id: STR-20260719-sr-role-reversal-entry
type: strategy
status: hypothesis
asset_class: stocks
trade_style: swing
timeframe: daily
market_regime: ranging
core_idea: reversal
confidence: medium
evidence_links:
  - C065-previous-support-as-future-resistance-in-downtrend
  - C368-support-and-resistance
  - EN069-price-gaps-as-support-and-resistance-for-timing
  - RG035-combining-technical-factors-with-money-management-for-stop-p
  - RG032-3-to-1-reward-to-risk-ratio
  - RG037-use-protective-stops-to-limit-losses
  - INS-2026-07-19-layer-gap-and-role-reversal-levels-to-anchor-position-sized-
last_reviewed: 2026-07-19
created: 2026-07-19
updated: 2026-07-19
tags: [strategy, hypothesis, support-resistance, role-reversal, swing]
---

# Support/Resistance Role-Reversal Entry

## Thesis

When price violates a significant support level, that level becomes resistance — the role-reversal principle. Subsequent rallies back to the broken support (now resistance) offer a high-probability short entry with a tight, well-defined stop (just above the former support). The edge is amplified when an unfilled gap overhead coincides with the role-reversal zone, creating a dual-confirmed resistance ceiling. Position size is derived from the distance to the stop, keeping risk within the PS-001 1% limit. This strategy targets the first pullback-to-resistance after a breakdown, exploiting the tendency for prior buyers trapped at the old support to sell into the rally.

## Entry Criteria

- [ ] **Breakdown confirmed:** Price has broken below a significant support level (defined as a level with ≥2 prior touch points over ≥10 trading days) on the daily chart with a closing price below support — not just an intraday pierce.
- [ ] **Role-reversal zone identified:** The broken support level (now resistance) is clearly defined. Acceptable zone width: ≤ 2% of current price (tight), or ≤ 0.5 ATR(14).
- [ ] **Rally into zone:** After the breakdown, price rallies back toward the role-reversal zone. Entry is on a bearish reversal signal at the zone boundary (e.g., bearish engulfing candle, shooting star, RSI turning back from overbought, or price stalling at the zone with declining volume on the rally).
- [ ] **Volume confirmation (optional but preferred):** The rally back to the resistance zone occurs on declining volume, confirming lack of buying conviction. A volume increase on a bearish reversal bar strengthens the entry signal.
- [ ] **Gap confluence (if present):** If an unfilled overhead gap boundary coincides with the role-reversal zone (within the zone width), this creates a doubly-confirmed resistance level — prioritize these setups (see INS layer-gap insight).
- [ ] **No counter-trend weekly:** Weekly chart must not be in a clear uptrend. Strategy is only valid in downtrends or consolidating markets.

## Exit Criteria

- [ ] **Stop loss:** Placed just above the upper boundary of the role-reversal resistance zone (for shorts), or just above the gap upper boundary if gap is the primary anchor. Add ≥ 0.25 ATR(14) buffer above the zone to avoid being stopped by noise.
- [ ] **Take profit / target:** Next significant support level below entry (measured from prior swing lows, round numbers, or chart patterns). Minimum 3:1 R:R before entering (RG032).
- [ ] **Invalidation exit:** If price closes above the resistance zone with strong volume (confirming zone reclaimed), exit immediately — the role-reversal thesis is invalidated.
- [ ] **Time stop:** If price has not moved toward target within 8 trading days, exit regardless of P&L.
- [ ] **Trailing stop:** Once 50% of position closed at first target (2:1), trail remainder stop to break-even, then trail below each lower swing high.

## Risk Rules Applied

- [ ] PS-001: Max 1% capital risk per position (stop distance × shares ≤ 1% capital)
- [ ] PS-004: Position size calculated before entry: (1% capital) ÷ (stop − entry for shorts)
- [ ] LL-001: Daily loss limit 2% — stop trading for the day if hit
- [ ] PT-001: Paper mode minimum 30 days before live consideration
- [ ] RG032: 3:1 minimum R:R — do not enter if target < 3× stop distance
- [ ] RG037: Use protective stops to limit losses — stop is mandatory, not optional

## Supporting Evidence

- [[C065-previous-support-as-future-resistance-in-downtrend]] — Core role-reversal principle: violated support becomes resistance (Murphy)
- [[C368-support-and-resistance]] — Fundamental S/R concepts; significance increases with number of touches and time at level
- [[EN069-price-gaps-as-support-and-resistance-for-timing]] — Price gaps as discrete S/R zones; sell rally to gap lower end, stop above gap
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]] — Valid technical level anchors stop; stop distance determines position size
- [[RG032-3-to-1-reward-to-risk-ratio]] — Minimum 3:1 R:R required before any trade
- [[RG037-use-protective-stops-to-limit-losses]] — Protective stops are non-negotiable; remove emotion from exit decisions
- [[INS-2026-07-19-layer-gap-and-role-reversal-levels-to-anchor-position-sized-]] — Discovery insight: gap + role-reversal confluence creates doubly-confirmed resistance; tighter stop enables larger size at same risk

## Counter-Evidence

- [[E005-subjectivity-in-defining-significant-penetration]] — Determining a "valid" support break is subjective; minor violations may not constitute real breakdowns
- [[C088-return-move-after-breakout-bottom-vs-top]] — Return moves are common after breakouts but not guaranteed; the setup fails if no return move occurs
- [[RG006-two-thirds-retracement-as-critical-reversal-level]] — If price retraces more than two-thirds back into the prior range, the breakdown may be invalidating — extend stop or consider exit at the two-thirds level

## Backtest / Paper Trade Log

- Paper trade log: _not started — requires PT-001 (30 days minimum)_
- Backtest results: _not started — see US-014 for backtesting library selection_

## Change Log

| Date | Change | Trigger |
|------|--------|---------|
| 2026-07-19 | Strategy created | US-052 Living Strategy Layer; seeded from Murphy S/R notes + INS layer-gap insight |
