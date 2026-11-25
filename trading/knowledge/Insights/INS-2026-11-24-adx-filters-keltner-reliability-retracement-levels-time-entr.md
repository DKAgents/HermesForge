---
type: insight
date: 2026-11-24
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
# ADX filters Keltner reliability; retracement levels time entries

## Discovery Summary

E036 ADX-Based Indicator Selection states that when ADX is rising, moving-average-based indicators are preferred, and when ADX is falling, oscillators are preferred. Keltner Channels are an MA-based indicator built on EMA and ATR, so their trend and breakout signals should be trusted only when ADX confirms a trending regime. C050 Secondary Trend Retracement Range adds that corrections in a primary trend typically retrace one-third to two-thirds of the prior move, with 50% most common, providing a pullback zone to combine with ADX-confirmed Keltner setups.

## Trading Implication

Trade Keltner Channel breakout or trend signals only when ADX is rising; when ADX is falling, avoid them and favor oscillators. In rising-ADX trends, look for price to retrace between one-third and two-thirds of the prior move, preferably near 50%, before entering in the direction of the primary trend.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5
