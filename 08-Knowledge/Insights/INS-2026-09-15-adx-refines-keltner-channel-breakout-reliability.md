---
type: insight
date: 2026-09-15
actionability: 4
connection_type: adds_condition
domains: [edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Refines Keltner Channel Breakout Reliability

## Discovery Summary

E036 ADX-Based Indicator Selection states that when ADX is rising (trending market), moving average-based indicators are preferred. N190 Keltner Channels are volatility envelopes centered on an exponential moving average, making them a moving average-based indicator. This means the reliability of Keltner Channel breakouts is conditional on ADX trending up, otherwise false signals may increase.

## Trading Implication

Only trade Keltner Channel breakouts when ADX is rising; in ranging markets (ADX falling), ignore breakouts or use oscillators instead.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
