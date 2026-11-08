---
type: insight
date: 2026-11-07
actionability: 3
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
# ADX Regime Filters Keltner Channels; Retracements Time Entries

## Discovery Summary

E036 ADX-Based Indicator Selection says rising ADX favors moving-average-based indicators and falling ADX favors oscillators. Keltner Channels are MA/ATR-based, so their trend and breakout signals should be trusted only when ADX is rising. In a rising-ADX primary trend, Dow's secondary retracement range (one-third to two-thirds, ~50% common; Technical Analysis of the Financial Markets, pp. 61–80) can time entries as price pulls back toward the Keltner EMA or bands.

## Trading Implication

Use ADX as a regime filter: take Keltner channel signals only when ADX is rising, and switch to oscillators when ADX is falling. In trending conditions, enter on secondary retracements of roughly 33–66% toward the Keltner middle or lower band rather than chasing breakouts.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 3/5
