---
type: insight
date: 2026-08-31
actionability: 3
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
# ADX Filter for Keltner Channel Retracement Entries

## Discovery Summary

E036 notes that when ADX is rising, moving average-based indicators like Keltner Channels (N190) are preferred for trending markets. C050 defines that secondary trends retrace one-third to two-thirds of the prior move, commonly 50%. By combining these, a trader can use rising ADX to confirm a trending environment, wait for a pullback to the 50% retracement level, and then enter on a Keltner Channel breakout, filtering out low-probability counter-trend trades.

## Trading Implication

Only consider buying retracement pullbacks to the 50% level when ADX is rising, and trigger entry on a close above the upper Keltner Channel band to confirm resumption of the trend.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 3/5
