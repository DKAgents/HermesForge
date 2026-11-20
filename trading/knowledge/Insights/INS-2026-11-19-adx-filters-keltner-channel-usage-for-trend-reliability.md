---
type: insight
date: 2026-11-19
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
# ADX Filters Keltner Channel Usage for Trend Reliability

## Discovery Summary

E036 ADX-Based Indicator Selection states that when ADX is rising (trending market), moving average-based indicators are preferred; when ADX is falling (ranging), oscillators are preferred. N190 Keltner Channels are MA-based (EMA with ATR bands), so they fall into the preferred class during rising ADX. This creates a clear filter: Keltner Channels should be used only when ADX confirms a trend, otherwise oscillators are more appropriate. C050's retracement range (one-third to two-thirds, commonly 50%) can complement this by providing target levels within the trend.

## Trading Implication

A trader should check ADX direction before applying Keltner Channels—use them when ADX is rising, and switch to oscillators when ADX falls. Additionally, use secondary trend retracement levels (e.g., 50%) as profit targets when trading with Keltner Channel breakouts.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5
