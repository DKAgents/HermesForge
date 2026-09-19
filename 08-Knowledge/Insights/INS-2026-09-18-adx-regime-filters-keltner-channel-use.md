---
type: insight
date: 2026-09-18
actionability: 4
connection_type: creates_filter
domains: [edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# ADX Regime Filters Keltner Channel Use

## Discovery Summary

When ADX is rising (trending market), moving average-based indicators like Keltner Channels (which use an EMA and ATR) become more effective for identifying breakouts and trend continuation. The ADX-Based Indicator Selection (E036) provides a regime filter that improves the reliability of Keltner Channel signals. Conversely, in a falling ADX (ranging market), oscillators should be used instead, avoiding Keltner Channels.

## Trading Implication

Trader should only use Keltner Channels for entry signals when ADX is rising and above a threshold (e.g., 25), and switch to oscillators when ADX is falling or below 20.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5
