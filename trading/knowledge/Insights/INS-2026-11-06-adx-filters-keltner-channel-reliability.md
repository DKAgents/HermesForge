---
type: insight
date: 2026-11-06
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
# ADX Filters Keltner Channel Reliability

## Discovery Summary

E036 states that rising ADX favors moving-average-based indicators, while falling ADX favors oscillators. Keltner Channels (N190) are built on an EMA and ATR, making them a MA-based volatility envelope. Therefore, Keltner Channel signals (e.g., price holding above/below the middle band or penetrating an outer band) are only reliable when ADX is rising. Additionally, C050 notes that secondary corrections in a trend retrace 1/3 to 2/3 of the prior move, often near 50%; this allows a trader to combine a trending regime (ADX rising) with Keltner band support/resistance to time entries at pullback levels within the channel.

## Trading Implication

Before acting on a Keltner Channel signal, check ADX: only trade the signal when ADX is rising; if ADX is falling, ignore the signal and switch to oscillators. In trending regimes, use the secondary retracement range (1/3–2/3, especially 50%) as a confluence zone for entries when price touches the Keltner middle or opposite band.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5
