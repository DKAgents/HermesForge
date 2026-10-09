---
type: insight
date: 2026-09-30
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
# ADX filters Keltner Channel reliability

## Discovery Summary

E036 ADX-based indicator selection suggests using ADX to identify trending vs. ranging markets. N190 Keltner Channels generate signals based on price crossing a moving average within a volatility envelope. C050 secondary-trend retracement range implies that retracements are less deep in strong trends. Combined, ADX > 25 indicates a strong trend where Keltner channel breakouts are more reliable, while ADX < 20 warns of choppy conditions where false signals occur.

## Trading Implication

A trader should only take Keltner Channel breakout or MA crossover signals when ADX is above 25, and consider fading signals when ADX is below 20 in favor of mean-reversion strategies.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
- [[INS-2026-09-07-adx-filters-keltner-channel-breakouts-by-trend-validity|ADX filters Keltner Channel breakouts by trend validity]]
