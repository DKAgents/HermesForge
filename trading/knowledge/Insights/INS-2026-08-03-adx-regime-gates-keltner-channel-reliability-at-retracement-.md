---
type: insight
date: 2026-08-03
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
# ADX Regime Gates Keltner Channel Reliability at Retracement Zones

## Discovery Summary

E036 establishes that ADX rising favors MA-based indicators, while ADX falling favors oscillators. Keltner Channels (N190) are MA-based (EMA core with ATR bands), meaning they are most reliable as trend/breakout tools when ADX is rising. C050 identifies that secondary retracements cluster at 33%-67% of prior move, creating predictable price zones. Combining these: when ADX is rising (trending regime confirmed), a price pullback into a 50% Fibonacci retracement that coincides with the Keltner Channel EMA midline or lower band provides a high-confidence MA-based entry signal — whereas in a falling ADX environment, the same Keltner touch should be ignored in favor of oscillator signals.

## Trading Implication

Only take Keltner Channel bounce or breakout trades when ADX is rising; additionally, prioritize entries where the channel midline or lower band aligns with the 33%-50% retracement of the prior swing to stack confluence conditions.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
