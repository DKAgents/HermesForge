---
type: insight
date: 2026-11-27
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
# ADX Rising Filter for Keltner Channel Trend Trades

## Discovery Summary

ADX-Based Indicator Selection (E036) states that MA-based indicators are preferred when ADX is rising, making the EMA-based Keltner Channels only reliable in trending regimes. The Secondary Trend Retracement Range (C050) notes that corrections typically retrace one-third to two-thirds of the prior move. Combining these, a trader can use rising ADX to validate that a pullback into the Keltner channel band within that retracement zone is a trend continuation rather than a range-bound signal.

## Trading Implication

Only take Keltner channel pullback entries when ADX is rising, and prioritize trades that align with a 50% retracement of the prior trend move; avoid Keltner signals when ADX is falling.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5
