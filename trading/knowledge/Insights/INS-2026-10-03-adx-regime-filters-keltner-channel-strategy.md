---
type: insight
date: 2026-10-03
actionability: 3
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Regime Filters Keltner Channel Strategy

## Discovery Summary

E036 (ADX-based indicator selection) provides a regime filter that determines whether to use Keltner channels (N190) for trend-following breakouts or mean-reversion trades at the channel boundaries. The secondary trend retracement range (C050) offers specific pullback levels within the channel when ADX is strong, making the combination a multi-condition setup.

## Trading Implication

Traders should first check ADX level; if >25, use Keltner channel breakouts with retracement to secondary trend range as entries; if <20, fade channel touches for reversals.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 3/5
