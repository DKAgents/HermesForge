---
type: insight
date: 2026-11-11
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
# ADX Filters Keltner/MA Signals; Retracement Sets Entries

## Discovery Summary

E036 ADX-Based Indicator Selection says rising ADX favors moving-average-based indicators, which directly applies to N190 Keltner Channels since they are built on an EMA. In trending conditions, C050 Secondary Trend Retracement Range gives a 1/3-to-2/3 pullback zone, often near 50%, that can align with Keltner band entries. When ADX is falling, Keltner/MA signals should be filtered out in favor of oscillators.

## Trading Implication

Before taking a Keltner Channel or MA crossover signal, require ADX to be rising; if ADX is falling, ignore these signals and trade oscillators. In an ADX-rising trend, use Keltner bands as the entry zone and expect pullbacks to retrace roughly 50% of the prior move before continuation.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5
