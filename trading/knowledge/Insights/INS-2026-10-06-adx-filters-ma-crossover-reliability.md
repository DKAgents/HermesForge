---
type: insight
date: 2026-10-06
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
# ADX filters MA crossover reliability

## Discovery Summary

E036-adx-based-indicator-selection suggests using ADX to select indicators; combining with C050-secondary-trend-retracement-range implies ADX regime determines trend strength. N190-keltner-channels provide volatility context, but the core insight is that ADX regime detection informs when MA crossovers are reliable, filtering out whipsaws in low-ADX periods.

## Trading Implication

Only trade MA crossover signals when ADX is above 25 (strong trend) and avoid them when ADX is below 20 (weak trend), using the secondary trend retracement range for entry timing.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 3/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
