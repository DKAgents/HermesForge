---
type: insight
date: 2026-09-14
actionability: 4
connection_type: adds_condition
domains: [concepts, edge_conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# ADX + Keltner Channels for Regime Filter

## Discovery Summary

E036 (ADX-Based Indicator Selection) states that when ADX is rising, moving average-based indicators are preferred, and Keltner Channels (N190) are built on an exponential moving average and ATR, making them trend-following tools. C050 (Secondary Trend Retracement Range) provides retracement targets (one-third to two-thirds) that can be used with Keltner Channels to set exit or entry zones during trending markets confirmed by a rising ADX. The non-obvious connection is that ADX regime detection tells you when Keltner Channel breakouts are reliable versus when they should be ignored as whipsaws in ranging markets.

## Trading Implication

Trade Keltner Channel breakouts (e.g., price closing outside the bands) only when ADX is rising and above 25; in ranging markets with falling ADX, use oscillators or skip Keltner-based entries, and use retracement levels from C050 to take partial profits.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[INS-2026-09-07-adx-filters-keltner-channel-breakouts-by-trend-validity|ADX filters Keltner Channel breakouts by trend validity]]
