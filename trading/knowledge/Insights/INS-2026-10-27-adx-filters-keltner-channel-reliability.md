---
type: insight
date: 2026-10-27
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
# ADX filters Keltner channel reliability

## Discovery Summary

E036-adx-based-indicator-selection suggests using ADX to identify trend strength. N190-keltner-channels provide volatility-based breakout signals. C050-secondary-trend-retracement-range defines typical pullbacks within larger trends. Combining them, a high ADX regime validates Keltner channel breakouts as genuine trend moves, while low ADX indicates range-bound conditions where breakouts are unreliable and retracements should be traded within the secondary trend range.

## Trading Implication

Trade Keltner channel breakouts only when ADX is above 25; when ADX is below 20, fade breakouts and instead trade mean reversion using the secondary trend retracement range for entries.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
