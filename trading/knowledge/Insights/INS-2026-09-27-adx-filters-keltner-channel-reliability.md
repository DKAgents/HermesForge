---
type: insight
date: 2026-09-27
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# ADX Filters Keltner Channel Reliability

## Discovery Summary

E036 (ADX-Based Indicator Selection) recommends using moving average-based indicators like Keltner Channels (N190) only when ADX is rising (trending market). When ADX is falling (ranging), oscillators are preferred. This adds a regime filter to Keltner Channel signals, improving reliability. The secondary retracement range (C050) is not directly linked but can inform target placement in trending markets.

## Trading Implication

Take Keltner Channel breakouts or EMA crossovers only when ADX is rising; in ranging markets, avoid Keltner signals and switch to oscillators.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[INS-2026-09-07-adx-filters-keltner-channel-breakouts-by-trend-validity|ADX filters Keltner Channel breakouts by trend validity]]
