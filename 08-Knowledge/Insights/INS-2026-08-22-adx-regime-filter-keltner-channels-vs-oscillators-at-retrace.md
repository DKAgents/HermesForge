---
type: insight
date: 2026-08-22
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# ADX Regime Filter: Keltner Channels vs Oscillators at Retracements

## Discovery Summary

E036-adx-based-indicator-selection establishes that rising ADX favors MA-based indicators while falling ADX favors oscillators. Keltner Channels (N190), being built on an EMA with ATR-based bands, are MA-based instruments and thus most reliable when ADX is rising — i.e., in trending conditions. C050 identifies that secondary corrections retrace 33-67% of the prior move, creating a high-probability zone where traders must choose between trend-continuation and mean-reversion tools. Combining all three: when price pulls back into the 1/3 to 2/3 Fibonacci retracement zone, ADX direction should determine whether to use Keltner Channel band tests (ADX rising — treat band touch as trend continuation entry) or oscillators (ADX falling — treat the retracement as a potential range trade).

## Trading Implication

When price enters the 33-67% secondary retracement zone, check ADX direction first: if ADX is rising, use Keltner Channel lower band touches as trend-continuation long entries; if ADX is falling, switch to oscillator-based signals and avoid fading the Keltner bands as trend proxies.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
