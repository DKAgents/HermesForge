---
type: insight
date: 2026-10-07
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
# ADX filters Keltner channel use with retracement

## Discovery Summary

Keltner channels (N190) provide volatility envelopes. The ADX-based indicator selection rule (E036) suggests using trend-following tools when ADX is high and mean-reversion tools when ADX is low. Combining these, a trader can filter Keltner channel use: breakouts on high ADX, mean reversion on low ADX. The secondary-trend-retracement range (C050) then refines entry levels within the channel during low-ADX regimes.

## Trading Implication

When ADX > 25, trade breakouts from Keltner channel boundaries; when ADX < 20, trade mean reversion at channel edges, using retracement levels of the secondary trend for precise entries.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 3/5
