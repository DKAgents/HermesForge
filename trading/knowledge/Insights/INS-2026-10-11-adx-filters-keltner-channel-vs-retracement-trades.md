---
type: insight
date: 2026-10-11
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
# ADX filters Keltner Channel vs retracement trades

## Discovery Summary

E036 ADX-based indicator selection recommends using ADX to gauge trend strength. N190 Keltner Channels work best for breakout trades in strong trends, while C050 secondary trend retracement range is suited for mean-reversion in weak trends. By combining them, a trader can filter trades: use Keltner breakouts when ADX is high (e.g., >25) and trade retracements to the secondary trend range when ADX is low.

## Trading Implication

Set an ADX threshold to decide between two strategies: above threshold, enter on Keltner channel breakouts; below, enter on retracements to the secondary trend range.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 3/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
- [[INS-2026-10-07-secondary-trend-retracement-zone-entry-filter|Secondary trend retracement zone entry filter]]
