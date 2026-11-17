---
type: insight
date: 2026-11-16
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
# ADX regime filter for Keltner retracement trades

## Discovery Summary

E036 ADX-Based Indicator Selection says moving-average-based indicators are preferred only when ADX is rising. N190 Keltner Channels is an MA-based, ATR-adjusted envelope, so its signals should be treated as valid only in rising-ADX trending regimes. C050 Secondary Trend Retracement Range (pages 61–80) then provides the entry logic: in a confirmed primary trend, enter on secondary corrections retracing one-third to two-thirds of the prior move. Together, rising ADX filters the market regime, and the Keltner band's EMA/ATR envelope supplies a dynamic price zone for executing those retracement entries.

## Trading Implication

Before acting on Keltner Channel breakouts or pullbacks, confirm ADX is rising; then limit entries to pullbacks that retrace roughly 33–66% of the prior swing, using the Keltner bands as the objective execution zone.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5
