---
type: insight
date: 2026-10-18
actionability: 3
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# ADX filters Keltner channel reliability regime

## Discovery Summary

E036-ADX-based-indicator-selection suggests using ADX to choose between trend and mean-reversion indicators. N190-Keltner-channels can generate both breakout (trend) and reversal (mean-reversion) signals. C050-secondary-trend-retracement-range provides typical retracement levels. The non-obvious connection is that ADX regime (e.g., above 25 vs below 20) determines which Keltner channel signals are reliable, with breakouts favored in strong trends and retracement entries in weak trends.

## Trading Implication

Use ADX to filter Keltner channel signals: take breakout trades only when ADX > 25; use retracements to the middle or opposite band when ADX < 20, combined with secondary retracement levels for entry.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 3/5
