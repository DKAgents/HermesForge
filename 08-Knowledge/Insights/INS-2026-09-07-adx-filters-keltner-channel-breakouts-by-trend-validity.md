---
type: insight
date: 2026-09-07
actionability: 3
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX filters Keltner Channel breakouts by trend validity

## Discovery Summary

E036 states rising ADX favors moving average-based indicators, while N190's Keltner Channels use an EMA as their centerline. C050 notes secondary trend retracements range from one-third to two-thirds, meaning a Keltner breakout during a falling ADX (ranging market) may merely be a retracement hitting the band rather than a true breakout. Combining these: only trade Keltner Channel breakouts when ADX is rising, otherwise interpret band touches as retracement targets within the one-third to two-thirds zone.

## Trading Implication

Before taking a Keltner Channel breakout trade, check ADX direction — if ADX is falling, treat the band touch as a potential retracement completion (50% mean), not a breakout entry signal.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 3/5
