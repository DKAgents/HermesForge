---
type: insight
date: 2026-11-18
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
# ADX Regime Filter for Keltner/MA Retracement Entries

## Discovery Summary

ADX-based indicator selection (E036) dictates using moving average-based indicators in trending regimes and oscillators in ranging ones. Keltner Channels (N190) are a trend/breakout tool that performs poorly in ranges where price oscillates between bands. When ADX is rising and price retraces into the Keltner middle EMA, the secondary retracement range (C050: one-third to two-thirds, ~50% typical) becomes a high-probability entry zone, because the ADX filter confirms the trend context. This combines regime detection with retracement entries to avoid false breakouts.

## Trading Implication

When ADX is rising and price pulls back to the Keltner middle EMA within the 33-66% retracement zone of the prior move, enter in the trend direction. Avoid entries when ADX is falling unless using an oscillator-based setup.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[INS-2026-11-08-adx-filter-confirms-keltner-pullback-entries-in-trends|ADX Filter Confirms Keltner Pullback Entries in Trends]]
