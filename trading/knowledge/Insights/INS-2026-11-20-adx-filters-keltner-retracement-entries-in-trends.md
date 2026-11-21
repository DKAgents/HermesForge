---
type: insight
date: 2026-11-20
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
# ADX Filters Keltner Retracement Entries in Trends

## Discovery Summary

E036-ADX-Based Indicator Selection establishes that MA-based indicators are only reliable while ADX is rising, and Keltner Channels are volatility envelopes around an EMA, so they belong in that trending-regime class. Once ADX confirms a trending market, C050-Secondary Trend Retracement Range supplies the entry trigger: corrections typically retrace one-third to two-thirds of the prior move, with 50% being most common. Together ADX acts as a filter for using Keltner/MA signals, and the retracement range sets the price zone for entries in the trend direction.

## Trading Implication

Use Keltner/MA-based signals only when ADX is rising; if ADX is falling, switch to oscillators. In a rising-ADX trend, place entries on pullbacks to the 50% retracement of the prior move instead of chasing breakouts.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5
