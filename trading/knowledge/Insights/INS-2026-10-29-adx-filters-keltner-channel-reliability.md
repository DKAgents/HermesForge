---
type: insight
date: 2026-10-29
actionability: 3
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# ADX filters Keltner channel reliability

## Discovery Summary

ADX-based indicator selection (E036) can determine when Keltner channels (N190) produce valid breakout signals: in high-ADX trending regimes, price moves beyond the channel bands are more likely to continue, while in low-ADX ranges, mean reversion to the centerline or secondary trend retracement zones (C050) offer better entries. This non-obviously links trend strength to channel-based trade timing.

## Trading Implication

Traders should use ADX > 25 to favor Keltner breakout trades and ADX < 20 to favor mean reversion or pullback trades using secondary retracement levels.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 3/5

## Related Notes
- [[INS-2026-10-07-secondary-trend-retracement-zone-entry-filter|Secondary trend retracement zone entry filter]]
