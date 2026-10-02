---
type: insight
date: 2026-10-02
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX filters Keltner Channel midline reliability

## Discovery Summary

E036 uses ADX to select indicators based on trend strength; N190 Keltner Channels rely on a moving average midline. When ADX is low, the midline is unreliable for trend direction, making Keltner breakouts or mean reversion less effective. C050 secondary trend retracement range can complement Keltner bands for defining retracement targets in trending regimes.

## Trading Implication

Only take Keltner Channel breakout signals when ADX > 25, and avoid trading based on the midline when ADX < 20.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
