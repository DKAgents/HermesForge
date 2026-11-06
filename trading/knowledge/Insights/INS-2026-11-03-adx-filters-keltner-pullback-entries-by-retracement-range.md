---
type: insight
date: 2026-11-03
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
# ADX Filters Keltner Pullback Entries by Retracement Range

## Discovery Summary

Keltner Channels are MA/ATR-based indicators, and ADX-Based Indicator Selection states that MA-based indicators are only preferred when ADX is rising (trending). This means Keltner Channel signals are reliable only in trending regimes. Secondary Trend Retracement Range adds that corrections retrace 1/3 to 2/3 of the prior move, most commonly 50%, so in a rising-ADX trend, a pullback to Keltner support within that range is a high-probability continuation entry.

## Trading Implication

When ADX is rising, take long entries on Keltner Channel pullbacks that retrace between one-third and two-thirds of the prior upswing; when ADX is falling, avoid Keltner signals and use oscillators instead.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
- [[INS-2026-10-24-adx-filter-for-keltner-channel-pullback-entries|ADX filter for Keltner channel pullback entries]]
