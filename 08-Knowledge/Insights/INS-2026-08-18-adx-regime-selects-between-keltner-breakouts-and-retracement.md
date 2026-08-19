---
type: insight
date: 2026-08-18
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
# ADX Regime Selects Between Keltner Breakouts and Retracement Oscillators

## Discovery Summary

E036-adx-based-indicator-selection establishes that rising ADX favors MA-based indicators while falling ADX favors oscillators. Keltner Channels (N190), being MA-plus-ATR envelope tools, fall into the MA-based category and are therefore most reliable when ADX is rising. When ADX is falling (ranging), C050-secondary-trend-retracement-range suggests that 33-67% Fibonacci retracement zones become the operative framework instead of Keltner breakout signals. This creates a two-regime system: ADX rising = trade Keltner breakouts; ADX falling = fade moves to 50% retracement levels.

## Trading Implication

A trader should activate Keltner Channel breakout entries only when ADX is rising, and switch to fading price moves at the 1/3-to-2/3 retracement zone (per Dow) when ADX is falling or flat — avoiding Keltner signals entirely in the ranging regime.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
