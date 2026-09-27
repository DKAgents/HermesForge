---
type: insight
date: 2026-08-04
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

E036-adx-based-indicator-selection establishes that ADX determines whether MA-based indicators (trending) or oscillators (ranging) are appropriate. Keltner Channels (N190) are MA-based volatility envelopes, making them valid only in ADX-rising trending conditions. C050 identifies that secondary corrections retrace 33-67% of prior moves — these retracement zones are precisely where ADX may be falling (correction = ranging), meaning Keltner Channels would be unreliable there and oscillators should replace them for timing entries at retracement levels.

## Trading Implication

At Fibonacci/Dow retracement zones (33-67% of prior move), check ADX direction before applying Keltner Channels: if ADX is falling during the correction, switch to oscillators for entry timing rather than relying on Keltner band touches as signals.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
