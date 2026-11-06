---
type: insight
date: 2026-10-30
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
# ADX regime filter makes MA crossovers reliable

## Discovery Summary

E036-adx-based-indicator-selection suggests using ADX to classify trend strength and choose between trend-following and mean-reverting tools. In strong-trend regimes, MA crossovers and Keltner channel breakouts (N190-keltner-channels) become trustworthy; in weak/choppy regimes, price is more likely to respect secondary trend retracement ranges (C050-secondary-trend-retracement-range), making mean-reversion strategies more effective. The non-obvious bridge is that ADX is a meta-filter: it determines whether MA-based signals should be acted upon or ignored, rather than being a standalone signal.

## Trading Implication

Before trading an MA crossover or Keltner breakout, check ADX; if ADX is rising/above a threshold, take trend signals, but if ADX is low or falling, fade moves back toward the secondary trend retracement range.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
