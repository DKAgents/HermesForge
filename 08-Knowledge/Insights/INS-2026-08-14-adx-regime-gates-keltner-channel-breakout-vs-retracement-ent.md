---
type: insight
date: 2026-08-14
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
# ADX Regime Gates Keltner Channel Breakout vs Retracement Entries

## Discovery Summary

E036 establishes that ADX rising favors MA-based indicators while ADX falling favors oscillators. Keltner Channels (N190) are MA-based (EMA core with ATR bands), making them most reliable precisely when ADX is rising — i.e., in trending conditions where breakouts from the channel are meaningful. C050 adds that secondary corrections retrace 1/3 to 2/3 of prior moves, meaning when ADX is falling (correction phase), traders should not rely on Keltner breakouts but instead anticipate mean-reversion entries toward the EMA core within the Fibonacci retracement zone.

## Trading Implication

Use Keltner Channel breakouts as trend-continuation entries only when ADX is rising; when ADX is falling, switch to fading price at the outer Keltner bands while targeting the 50% Dow retracement level as the profit objective.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
