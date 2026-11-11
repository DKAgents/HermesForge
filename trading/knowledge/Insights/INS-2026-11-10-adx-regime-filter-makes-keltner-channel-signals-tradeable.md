---
type: insight
date: 2026-11-10
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "C050-secondary-trend-retracement-range", "E036-adx-based-indicator-selection"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# ADX regime filter makes Keltner Channel signals tradeable

## Discovery Summary

ADX-Based Indicator Selection states that moving-average-based indicators are preferred only when ADX is rising, while oscillators are preferred when ADX is falling. Keltner Channels are built on an EMA and ATR, making them an MA-based indicator whose signals should be filtered by the ADX regime. Secondary Trend Retracement Range adds that corrections in a trending market typically retrace one-third to two-thirds of the prior move, commonly 50%, which gives a concrete pullback zone around the Keltner middle EMA for entries.

## Trading Implication

Before acting on a Keltner Channel signal, check ADX: only trade Keltner pullbacks or breakouts when ADX is rising, and use the 1/3–2/3 retracement zone as the entry area in the direction of the primary trend. When ADX is falling, ignore Keltner Channels and switch to oscillators.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
