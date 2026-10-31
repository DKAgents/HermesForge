---
type: insight
date: 2026-10-22
actionability: 4
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
# ADX filters Keltner and MA trend signals

## Discovery Summary

E036-adx-based-indicator-selection implies ADX regime should govern whether trend-following indicators are reliable. N190-keltner-channels is a volatility/MA-based indicator whose breakouts can be either trend signals or range extremes depending on that regime. C050-secondary-trend-retracement-range provides the pullback zone where a filtered trend signal becomes an actionable entry or stop placement. Together, ADX acts as a gate: strong ADX validates Keltner/MA trend signals, while weak ADX makes them unreliable and better treated as mean-reversion clues.

## Trading Implication

Before acting on Keltner channel breakouts or MA crossovers, check ADX and trade the trend direction only when ADX confirms a trending regime; in low ADX, fade the bands or use retracement-range mean-reversion instead.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[INS-2026-09-08-adx-validates-when-keltner-channels-are-actionable|ADX validates when Keltner Channels are actionable]]
