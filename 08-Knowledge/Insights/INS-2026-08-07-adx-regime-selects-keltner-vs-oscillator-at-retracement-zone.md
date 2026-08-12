---
type: insight
date: 2026-08-07
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
# ADX Regime Selects Keltner vs Oscillator at Retracement Zones

## Discovery Summary

E036 establishes that ADX direction determines whether trend-following or oscillator tools are appropriate. N190 describes Keltner Channels as MA-based volatility envelopes — per E036's logic, these are only reliable in rising-ADX (trending) conditions. C050 identifies that secondary retracements commonly end at the 33%-67% zone, creating a specific price location to apply the ADX filter: at a Dow retracement level, check ADX direction before choosing between Keltner Channel mean-reversion signals (falling ADX) or Keltner breakout/trend continuation signals (rising ADX).

## Trading Implication

When price pulls back to the 33%-67% Fibonacci/Dow retracement zone, a trader should first check ADX direction: if ADX is rising, use Keltner Channel band tests as trend-continuation entries; if ADX is falling, switch to an oscillator for mean-reversion entries at that same retracement level rather than relying on Keltner signals.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
