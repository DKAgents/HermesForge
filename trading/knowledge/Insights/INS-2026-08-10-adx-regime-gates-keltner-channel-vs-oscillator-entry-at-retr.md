---
type: insight
date: 2026-08-10
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
# ADX Regime Gates Keltner Channel vs Oscillator Entry at Retracement Zones

## Discovery Summary

E036-adx-based-indicator-selection establishes that ADX regime determines whether MA-based or oscillator-based tools are appropriate. Keltner Channels (N190) are MA-based (EMA + ATR bands), making them valid only in trending regimes per the ADX rule. C050 identifies that secondary corrections retrace 33-67% of prior moves, creating predictable price zones where trend resumption may occur — but only Keltner Channel mean-reversion signals at those zones should be acted upon when ADX confirms trending conditions; otherwise oscillators should be used at the same retracement levels.

## Trading Implication

When price retraces to the 33-67% Fibonacci zone (C050), check ADX first: if ADX is rising, use Keltner Channel band touches as trend-resumption entries; if ADX is falling, switch to oscillators at those same retracement levels instead of relying on Keltner bands.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
