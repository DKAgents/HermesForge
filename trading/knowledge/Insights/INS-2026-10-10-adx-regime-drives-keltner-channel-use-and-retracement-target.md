---
type: insight
date: 2026-10-10
actionability: 3
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX regime drives Keltner Channel use and retracement targets

## Discovery Summary

The ADX-based indicator selection (E036) identifies trend strength, which filters whether to use Keltner Channels (N190) for breakouts (strong trend) or mean reversion (weak trend). The secondary trend retracement range (C050) then provides precise entry and exit zones within that regime, creating a systematic rule set.

## Trading Implication

Traders should measure ADX first: if above 25, trade Keltner Channel breakouts; if below 20, fade the edges toward the secondary retracement range.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 3/5
