---
type: insight
date: 2026-10-04
actionability: 3
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Filter for Keltner Channel Breakouts

## Discovery Summary

E036 (ADX-based indicator selection) suggests using ADX to determine when trend-following indicators are reliable. N190 (Keltner Channels) is a volatility-based envelope that works best in trending markets. C050 (secondary trend retracement range) provides context for retracements within a trend. Together, ADX can filter Keltner Channel breakouts: high ADX (>25) increases reliability, while low ADX (<20) warns of false signals.

## Trading Implication

Only trade Keltner Channel breakouts when ADX is above 25, indicating a strong trend; avoid signals when ADX is below 20, as markets are likely ranging and breakouts may fail.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 3/5
