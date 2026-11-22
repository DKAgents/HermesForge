---
type: insight
date: 2026-11-21
actionability: 4
connection_type: confirms_risk_rule
domains: [position_sizing, price_gaps, risk_guidelines, support_resistance]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "EN069-price-gaps-as-support-and-resistance-for-timing"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Violated Support and Gaps Set Stops for Position Sizing

## Discovery Summary

C065 and EN069 both provide objective support/resistance levels from price action: violated support becomes resistance in downtrends, and gaps act as support/resistance after moves. EN069 explicitly places protective stops beyond these levels (below gap support, above gap resistance), while C065 implies the same for short entries at former support. The connecting risk rule is that each S/R level defines the stop distance, and stop distance then determines position size for a given risk amount. This unifies Murphy's price levels with position-sizing discipline on both long and short sides.

## Trading Implication

Before entering, identify the relevant S/R level (old support in a downtrend, gap edge after a trend), place the stop just beyond it, and size the position so the stop-distance loss equals your predefined risk. Use the same procedure for short entries into old support/gap resistance and long entries into gap support.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[C334-resistance-level|Resistance Level]]
