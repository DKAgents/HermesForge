---
type: insight
date: 2026-10-19
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# ADX filters Keltner channel strategy regime

## Discovery Summary

E036 suggests ADX regime determines which indicators are effective. N190 Keltner channels are volatility-based with a central MA. C050 secondary trend retracement range provides typical pullback levels. The non-obvious insight: when ADX is high (trending), Keltner channel breakouts become reliable; when low (ranging), mean-reversion bounces off the bands are more effective, using the retracement range as confirmation.

## Trading Implication

A trader should filter Keltner channel trades by ADX: use breakout entries above/below bands when ADX > 25, and mean-reversion entries from band touches when ADX < 20.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
