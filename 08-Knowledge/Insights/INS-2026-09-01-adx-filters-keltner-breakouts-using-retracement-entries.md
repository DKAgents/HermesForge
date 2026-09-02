---
type: insight
date: 2026-09-01
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# ADX Filters Keltner Breakouts Using Retracement Entries

## Discovery Summary

E036 states that rising ADX favors moving-average-based indicators, and N190's Keltner Channels rely on an exponential moving average. Thus, ADX regime can filter Keltner Channel breakout signals for reliability. C050's retracement range (1/3 to 2/3) then provides a precise entry zone within the trending environment, tightening risk management.

## Trading Implication

Only trade Keltner Channel breakouts when ADX is rising, and enter on pullbacks to the 50% retracement of the prior swing for improved risk/reward.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5
