---
type: insight
date: 2026-11-09
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, position_sizing, risk_management, rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "EN069-price-gaps-as-support-and-resistance-for-timing"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# S/R Levels Set Stops, Which Size Positions

## Discovery Summary

C065 (previous support as future resistance) and EN069 (price gaps as support/resistance) both provide objective price levels for entering with a protective stop just beyond the level. In a downtrend, shorting at former support-turned-resistance or at the lower edge of a gap defines a specific stop distance. That stop distance determines risk per share, which under a fixed fractional risk model dictates position size. This connects Murphy's S/R rules directly to risk management.

## Trading Implication

When shorting at a resistance level from C065 or EN069, measure the distance from entry to the stop above that level and use it to size the position so each trade risks a consistent fraction of equity.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[INS-2026-09-22-s-r-stop-distance-determines-position-size|S/R Stop Distance Determines Position Size]]
- [[C334-resistance-level|Resistance Level]]
