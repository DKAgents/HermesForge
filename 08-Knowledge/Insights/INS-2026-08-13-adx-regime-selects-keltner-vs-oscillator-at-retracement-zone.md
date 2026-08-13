---
type: insight
date: 2026-08-13
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Regime Selects Keltner vs Oscillator at Retracement Zones

## Discovery Summary

E036 establishes that ADX rising favors MA-based indicators while ADX falling favors oscillators. Keltner Channels (N190) are MA-based (EMA + ATR bands), making them most reliable in trending regimes per E036's logic. C050 identifies that secondary retracements of 33-67% are predictable correction zones within primary trends — precisely where a trader must decide whether to use a trend-following tool like Keltner Channels or an oscillator. Combining these three: when price enters a 33-67% retracement zone (C050), check ADX direction first (E036) — only deploy Keltner Channel breakout signals (N190) if ADX is rising, confirming the primary trend is still intact and MA-based tools are appropriate.

## Trading Implication

At Fibonacci/Dow retracement levels (33-67% of prior move), use ADX direction to gate indicator selection: if ADX is rising, use Keltner Channel band tests as re-entry signals with the primary trend; if ADX is falling, switch to oscillators to fade the range instead.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
