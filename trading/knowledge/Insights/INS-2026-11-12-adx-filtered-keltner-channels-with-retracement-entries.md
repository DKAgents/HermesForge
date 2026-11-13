---
type: insight
date: 2026-11-12
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
# ADX-Filtered Keltner Channels with Retracement Entries

## Discovery Summary

ADX-Based Indicator Selection (E036) states that rising ADX favors moving average-based indicators, while falling ADX favors oscillators. Keltner Channels (N190) are constructed with an EMA and ATR, making them an MA-based trend-following indicator, so their breakout signals are only reliable when ADX is rising. Once ADX confirms a trending regime, Secondary Trend Retracement Range (C050) provides specific pullback zones—one-third to two-thirds of the prior move, commonly 50%—for entries. Together, ADX filters when to use Keltner Channels, and the retracement range identifies high-probability entry levels within that filtered trend.

## Trading Implication

Only take Keltner Channel breakout or pullback signals when ADX is rising; in a confirmed uptrend, buy at the 50% retracement of the prior advance with the Keltner middle EMA as support. When ADX is falling, avoid Keltner-based signals and switch to oscillators.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5
