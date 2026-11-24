---
type: insight
date: 2026-11-23
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "C050-secondary-trend-retracement-range", "E036-adx-based-indicator-selection"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# ADX Regime Selects Keltner and Retracement Entries

## Discovery Summary

E036-adx-based-indicator-selection states that a rising ADX favors moving-average indicators, while a falling ADX favors oscillators. Keltner Channels (N190-keltner-channels) are built on an EMA, so their trend and breakout signals are only reliable in the rising-ADX regime. In that same trending regime, C050-secondary-trend-retracement-range provides a specific pullback zone — one-third to two-thirds, centered near 50% — where entries can be timed within the MA-based framework.

## Trading Implication

Use ADX as a filter before trading Keltner channel or MA-crossover pullbacks: only take long entries on 33–66% retracements when ADX is rising; when ADX is falling, abandon MA-based signals and switch to oscillators.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5
