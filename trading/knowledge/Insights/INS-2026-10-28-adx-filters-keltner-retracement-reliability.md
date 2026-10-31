---
type: insight
date: 2026-10-28
actionability: 3
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
# ADX filters Keltner retracement reliability

## Discovery Summary

E036-ADX-based-indicator-selection suggests using ADX to determine market regime. In strong trends (high ADX), N190-Keltner-channels provide reliable volatility-based support/resistance. C050-secondary-trend-retracement-range defines typical pullback levels within a trend. Combining them, a trader can use high ADX to confirm that Keltner channel boundaries are valid retracement targets, reducing false signals in choppy markets.

## Trading Implication

Only use Keltner channel levels as secondary trend retracement entries when ADX is above 25, ensuring the trend is strong enough to respect those bands.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 3/5
