---
type: insight
date: 2026-08-01
actionability: 4
connection_type: adds_condition
domains: [edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# ADX Regime Filter for Keltner Channel Breakout Validity

## Discovery Summary

E036-adx-based-indicator-selection establishes that ADX distinguishes trending from ranging regimes, recommending MA-based indicators during trends. Keltner Channels (N190) are MA-based (EMA core) with ATR-derived bands, making them directly subject to this regime filter. The non-obvious implication is that Keltner Channel breakouts should only be traded as trend-continuation signals when ADX is rising, while a falling ADX suggests Keltner bands should be treated as mean-reversion boundaries rather than breakout triggers.

## Trading Implication

A trader should require ADX to be rising before entering Keltner Channel breakout trades; when ADX is falling, fade price touches of the outer Keltner bands instead of following breakouts.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
