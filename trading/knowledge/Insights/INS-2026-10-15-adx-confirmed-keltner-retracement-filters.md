---
type: insight
date: 2026-10-15
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
# ADX-Confirmed Keltner Retracement Filters

## Discovery Summary

E036 adx-based-indicator-selection argues that indicator choice should be conditioned on ADX regime. N190 keltner-channels provide volatility-based support/resistance, while C050 secondary-trend-retracement-range defines the typical pullback zone within a larger trend. Combining these, Keltner Channel signals become reliable only when ADX confirms a trending regime, and entries should ideally occur within the secondary trend retracement range.

## Trading Implication

A trader should use ADX as a filter: take Keltner Channel breakouts or bounces only when ADX indicates a trend, and align those trades with the secondary trend retracement range to avoid false signals in choppy markets.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-07-secondary-trend-retracement-zone-entry-filter|Secondary trend retracement zone entry filter]]
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
