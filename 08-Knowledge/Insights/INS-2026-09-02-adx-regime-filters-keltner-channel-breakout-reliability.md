---
type: insight
date: 2026-09-02
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# ADX Regime Filters Keltner Channel Breakout Reliability

## Discovery Summary

E036 recommends using moving average-based indicators when ADX is rising. Since N190 Keltner Channels rely on an exponential moving average and ATR-based bands, their breakout signals gain reliability only in trending regimes (ADX rising). C050's secondary trend retracement range (⅓–⅔, typically 50%) describes how corrections often stay within the channel bands, offering a timing entry near the bands when ADX confirms trend resumption.

## Trading Implication

Only take Keltner Channel breakout signals when ADX is rising; use secondary trend retracements to the channel bands as entry triggers aligned with the primary trend.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5
