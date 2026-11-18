---
type: insight
date: 2026-11-17
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
# ADX Regime Filters Keltner Channel Reliability

## Discovery Summary

E036's ADX-Based Indicator Selection states that MA-based indicators are preferred when ADX is rising and oscillators when ADX is falling. Since Keltner Channels are an MA-based indicator built on an EMA and ATR, their breakout/trend signals should be taken only when ADX confirms a trending regime. C050's Secondary Trend Retracement Range then helps frame the post-breakout pullback: in a primary trend, secondary corrections typically retrace one-third to two-thirds (commonly ~50%), so a Keltner band/EMA retest inside that zone can serve as an entry or add-on location.

## Trading Implication

Before acting on Keltner Channel breakouts or EMA bounces, require rising ADX; when ADX is falling, ignore Keltner signals and use oscillators instead. In confirmed trends, treat Keltner-band/EMA bounces within the 1/3-to-2/3 retracement zone as high-probability re-entry points.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
