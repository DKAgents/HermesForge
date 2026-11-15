---
type: insight
date: 2026-11-14
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
# ADX Regime Filters Keltner Channel Breakout Reliability

## Discovery Summary

E036-ADX-Based Indicator Selection says rising ADX favors moving-average-based indicators and falling ADX favors oscillators. N190-Keltner Channels are a moving-average-based indicator (EMA with ATR bands), so ADX regime determines whether Keltner breakouts are meaningful. C050-Secondary Trend Retracement Range reinforces the context: one-third-to-two-third pullbacks are only meaningful within a confirmed trend, which is the same condition that makes Keltner valid. Thus ADX acts as a non-obvious filter for both Keltner signals and retracement entries.

## Trading Implication

Only trade Keltner Channel breakouts or secondary-retracement entries when ADX is rising/trending; when ADX is falling, ignore Keltner signals and switch to oscillators.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5
