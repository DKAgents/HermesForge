---
type: insight
date: 2026-09-10
actionability: 3
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Filters Keltner Entries at Secondary Retracements

## Discovery Summary

E036 states that rising ADX favors moving average-based indicators, making them more reliable in trending markets. Keltner Channels (N190) are such a moving average-based tool; when ADX confirms a trend, their signals gain validity. Within the trend, C050's secondary retracement range (one-third to two-thirds) identifies pullback levels, and the Keltner bands can act as dynamic support/resistance near these zones, creating a high-probability entry setup.

## Trading Implication

When ADX is rising, confirm trend direction with Keltner Channels, then wait for a pullback to the 50% retracement level that coincides with a Keltner band before entering in the trend direction.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 3/5
