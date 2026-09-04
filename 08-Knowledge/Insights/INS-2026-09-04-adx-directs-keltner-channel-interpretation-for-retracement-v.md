---
type: insight
date: 2026-09-04
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX directs Keltner Channel interpretation for retracement vs breakout

## Discovery Summary

E036 establishes that rising ADX favors moving-average-based indicators, which directly applies to Keltner Channels (N190) given their EMA core. When ADX is rising during a secondary retracement that holds within the one-third to two-thirds range (C050), the Keltner Channel bands can distinguish between a mere correction within the trend and a genuine breakout. The ATR component of Keltner Channels adapts the envelope width to current volatility, making band touches during ADX-confirmed trends actionable.

## Trading Implication

Monitor ADX direction: if rising, treat a price touch of the Keltner Channel band in direction of the primary trend during a 33-66% retracement as a trend-continuation entry, not a breakout signal.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5
