---
type: insight
date: 2026-08-05
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

E036 establishes that ADX determines whether trend-following indicators (like MAs/Keltner Channels from N190) or oscillators are appropriate. N190's Keltner Channels are MA-based volatility envelopes, making them valid only in trending (rising ADX) conditions. C050's 1/3 to 2/3 retracement range identifies where secondary corrections end — precisely the zones where ADX may be transitioning, meaning a trader must check ADX direction before applying Keltner Channel breakout signals at these retracement levels.

## Trading Implication

At Fibonacci/Dow retracement zones (33%-67% of prior move), check ADX direction before acting: if ADX is rising, use Keltner Channel band touch as a trend-continuation entry; if ADX is falling, switch to an oscillator for a range-bound mean-reversion trade instead.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
