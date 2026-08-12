---
type: insight
date: 2026-08-12
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Regime Selects Keltner vs Oscillator at Retracement Zones

## Discovery Summary

E036-adx-based-indicator-selection establishes that ADX rising favors MA-based indicators while ADX falling favors oscillators. Keltner Channels (N190) are MA-based (EMA + ATR bands), making them reliable only in trending regimes per ADX. C050 identifies that secondary corrections retrace 33-67% of prior moves — these retracement zones are precisely where traders must decide whether to use trend-following tools like Keltner Channels or oscillators. Combining all three: when price enters a Dow retracement zone (1/3 to 2/3 of prior move), check ADX direction — if ADX is still rising, Keltner Channel signals at the retracement zone are valid trend-continuation entries; if ADX is falling, switch to oscillators to trade the range within that retracement.

## Trading Implication

At 33-67% retracement levels, use ADX direction as a filter: enter Keltner Channel mean-reversion or breakout signals only when ADX is rising; if ADX is falling at the same retracement zone, ignore Keltner signals and apply oscillators instead.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
