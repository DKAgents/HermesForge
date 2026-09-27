---
type: insight
date: 2026-08-09
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

E036 establishes that ADX rising favors MA-based indicators while ADX falling favors oscillators. Keltner Channels (N190) are MA-based (EMA core with ATR bands), meaning they are most reliable as trend-following tools when ADX is rising. C050 identifies that secondary retracements typically reach 33-67% of the prior move — these retracement zones are precisely where a trader must decide whether to fade the move (oscillator logic) or hold with trend (MA logic). Combining all three: when price retraces to the Keltner Channel midline (EMA) within the 33-67% Fibonacci zone, ADX direction determines whether to treat the channel touch as a trend-continuation entry (ADX rising) or a potential reversal signal (ADX falling).

## Trading Implication

At a secondary retracement into the Keltner Channel EMA (within the 33-67% retracement range), only take the with-trend bounce entry if ADX is simultaneously rising; if ADX is falling, switch to oscillator-based counter-trend signals instead of trusting the channel.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
