---
type: insight
date: 2026-09-12
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Filter for Keltner Pullback Entries

## Discovery Summary

E036 states that when ADX is rising, moving-average-based indicators are preferred; Keltner Channels (N190) are EMA-based, so they become more reliable. C050 notes that corrections within a trend retrace one-third to two-thirds, commonly 50%. In a rising ADX environment, a pullback to the Keltner midline (the EMA) that coincides with a 50% retracement of the prior swing offers a high-probability trend-continuation entry zone, combining regime confirmation with a volatility envelope and Dow-based retracement levels.

## Trading Implication

Only consider pullback entries to the Keltner Channel centerline when ADX is rising; wait for price to tag both the midline and a 50% retracement of the prior trend leg for a filtered entry signal.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5
