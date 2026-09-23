---
type: insight
date: 2026-09-22
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
# ADX Filters Keltner Channel Reliability

## Discovery Summary

The ADX-Based Indicator Selection note states that when ADX is rising (trending market), moving average-based indicators are preferred. Keltner Channels are built on an exponential moving average, making them a moving average-based indicator. Therefore, ADX regime can serve as a filter: only act on Keltner Channel breakout or cross signals when ADX is rising, increasing their reliability.

## Trading Implication

A trader should monitor ADX direction and only take Keltner Channel signals (e.g., price closing above upper band) when ADX is rising, as this confirms a trending environment where such signals are more effective.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5
