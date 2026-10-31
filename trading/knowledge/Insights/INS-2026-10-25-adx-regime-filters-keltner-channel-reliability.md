---
type: insight
date: 2026-10-25
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
# ADX regime filters Keltner channel reliability

## Discovery Summary

E036 ADX-based indicator selection suggests using ADX to determine when indicators are effective. N190 Keltner channels provide volatility-based support and resistance levels. C050 secondary trend retracement range defines likely pullback zones. The non-obvious connection is that ADX regime (from E036) can filter when Keltner channel touches (N190) reliably identify retracement levels (C050), e.g., strong trends produce tighter channels that better define entries.

## Trading Implication

Use ADX to confirm trend strength before trading Keltner channel retracement signals; avoid Keltner-based entries when ADX is below 20.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 3/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
- [[C334-resistance-level|Resistance Level]]
