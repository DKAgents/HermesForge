---
type: insight
date: 2026-11-04
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "C050-secondary-trend-retracement-range", "E036-adx-based-indicator-selection"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# ADX Filter for Keltner Channel Retracements

## Discovery Summary

The ADX-based indicator selection rule (E036) states that moving average-based indicators like Keltner Channels (N190) are most effective in trending markets (rising ADX), while oscillators suit ranging markets. The secondary trend retracement range (C050) specifies that corrections typically retrace 1/3 to 2/3 of the prior move, often around 50%. Combining these, a trader can use a rising ADX to confirm that Keltner Channel pullback signals are valid, and target entries near the channel bands that align with typical retracement levels, especially the 50% level.

## Trading Implication

Only trade Keltner Channel pullbacks when ADX is rising, and use the channel band as a trigger zone that coincides with a 33-66% retracement of the prior leg, with a stop outside the channel.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**adds_condition** — Actionability score: 4/5
