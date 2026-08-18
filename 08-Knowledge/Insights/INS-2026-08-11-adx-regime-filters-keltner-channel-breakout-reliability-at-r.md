---
type: insight
date: 2026-08-11
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
# ADX Regime Filters Keltner Channel Breakout Reliability at Retracements

## Discovery Summary

E036-adx-based-indicator-selection establishes that ADX rising favors MA-based indicators while ADX falling favors oscillators. Keltner Channels (N190) are MA-based volatility envelopes, meaning they are most reliable as breakout/trend tools when ADX is rising. C050 identifies that secondary corrections retrace 33-67% of the prior move, creating specific price zones where ADX regime should be checked before applying Keltner Channel breakout signals — a rising ADX at the 50% retracement level confirms the primary trend is reasserting, making a Keltner upper-band breakout more actionable than the same signal during a falling ADX.

## Trading Implication

At Fibonacci/Dow retracement zones (33-67% of prior move), only trade Keltner Channel breakouts when ADX is simultaneously rising; a falling ADX at the same price level signals a ranging correction where Keltner breakouts are unreliable and an oscillator-based mean-reversion entry is preferable instead.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[INS-2026-08-17-adx-regime-filters-keltner-channel-breakout-signals-at-retra|ADX Regime Filters Keltner Channel Breakout Signals at Retracements]]
- [[INS-2026-08-01-adx-regime-filter-for-keltner-channel-breakout-validity|ADX Regime Filter for Keltner Channel Breakout Validity]]
