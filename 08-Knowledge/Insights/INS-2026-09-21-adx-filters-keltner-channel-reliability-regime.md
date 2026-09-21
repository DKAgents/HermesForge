---
type: insight
date: 2026-09-21
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Filters Keltner Channel Reliability Regime

## Discovery Summary

E036 states ADX rising favors trend-following tools like moving averages, while falling ADX favors oscillators. Keltner Channels (N190) are trend-following volatility envelopes built on an EMA and ATR. This creates a non-obvious filter: only trade Keltner breakouts when ADX is rising, avoiding false signals in ranging markets where oscillators would be more appropriate. The retracement range (C050) reinforces that during secondary corrections, Keltner bands may fail as breakout triggers until the primary trend resumes.

## Trading Implication

Add an ADX filter to Keltner Channel strategies: enter breakouts only when ADX is rising above 20, and ignore signals or switch to oscillators when ADX is flat or falling.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
