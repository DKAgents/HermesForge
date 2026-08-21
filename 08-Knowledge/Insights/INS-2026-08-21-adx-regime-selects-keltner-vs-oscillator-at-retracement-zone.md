---
type: insight
date: 2026-08-21
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Regime Selects Keltner vs Oscillator at Retracement Zones

## Discovery Summary

E036 establishes that ADX rising favors MA-based indicators while ADX falling favors oscillators. Keltner Channels (N190) are MA-based (EMA core with ATR bands), making them valid only in trending regimes per E036's rule. C050 identifies that secondary retracements cluster at 1/3, 1/2, and 2/3 of prior move — these are precisely the zones where ADX status determines whether to use Keltner band touches (trending) or oscillator extremes (ranging) as entry signals.

## Trading Implication

At a 33-50% retracement of a prior move, check ADX direction first: if ADX is rising, use Keltner Channel lower band touch as a trend-continuation entry; if ADX is falling, switch to an oscillator for a mean-reversion entry instead of relying on Keltner.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
