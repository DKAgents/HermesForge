---
type: insight
date: 2026-09-16
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX filter for Keltner Channel breakout signals

## Discovery Summary

ADX-Based Indicator Selection (E036) states that when ADX is rising (trending market), moving average-based indicators are preferred; Keltner Channels (N190) are a moving average-based envelope with ATR-set bands. During rising ADX, a Keltner channel breakout (price closing above upper band) is more likely to be a genuine trend continuation, while during falling ADX (ranging market), such breakouts are prone to false signals. The Secondary Trend Retracement Range (C050) also suggests that in the context of a secondary correction, a Keltner band reversion to the 50% retracement level could serve as a higher-probability entry when ADX confirms the primary trend.

## Trading Implication

When using Keltner Channels, only take long breakouts when ADX is rising and above a threshold (e.g., 25) to avoid whipsaws; in falling ADX, fade the bands or wait for ADX to turn up before entering.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
