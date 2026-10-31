---
type: insight
date: 2026-10-17
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
# ADX Filters Keltner Channel Breakout Reliability

## Discovery Summary

Using E036 (ADX-based indicator selection), high ADX indicates trending conditions where N190 (Keltner Channels) breakouts are reliable. C050 (secondary trend retracement range) then defines optimal entry zones within the trend, avoiding false signals from low-ADX range-bound markets.

## Trading Implication

Only trade Keltner Channel breakouts when ADX > 25, and use secondary trend retracement levels for entries to increase win rate.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
