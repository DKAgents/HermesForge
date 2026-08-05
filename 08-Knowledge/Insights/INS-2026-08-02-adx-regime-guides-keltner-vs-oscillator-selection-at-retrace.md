---
type: insight
date: 2026-08-02
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
# ADX Regime Guides Keltner vs Oscillator Selection at Retracements

## Discovery Summary

E036-adx-based-indicator-selection establishes that ADX rising favors MA-based indicators while ADX falling favors oscillators. Keltner Channels (N190) are MA-based envelopes — meaning they are most reliable in trending regimes. C050 identifies secondary trend retracements (33%-67% of prior move) as key inflection zones where the market may resume the primary trend or deepen the correction. The non-obvious connection is that ADX direction at the moment price enters a Dow retracement zone (C050) determines whether Keltner Channel signals at those levels are trustworthy: rising ADX validates Keltner breakout signals within the retracement zone, while falling ADX suggests switching to oscillators to trade the range instead.

## Trading Implication

When price pulls back into the 33%-67% Fibonacci retracement zone, check ADX direction first: if ADX is rising, use Keltner Channel breakout signals to enter trend resumption trades; if ADX is falling, ignore Keltner signals and use oscillators to fade the range boundaries instead.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
