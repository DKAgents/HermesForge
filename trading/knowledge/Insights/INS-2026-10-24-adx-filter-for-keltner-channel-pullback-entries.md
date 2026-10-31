---
type: insight
date: 2026-10-24
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
# ADX filter for Keltner channel pullback entries

## Discovery Summary

E036 (ADX-based indicator selection) suggests using ADX to determine trend strength. N190 (Keltner channels) uses EMA and ATR to identify volatility-based support/resistance. C050 (secondary trend retracement range) defines typical pullback distances within a trend. Combining them: high ADX (trending) makes Keltner channel breaks more reliable, and retracement range provides entry zones on pullbacks to the channel midline.

## Trading Implication

Only take Keltner channel breakout signals when ADX > 25, and place limit entries at the secondary retracement range within the channel during pullbacks.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
