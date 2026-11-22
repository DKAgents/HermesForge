---
type: insight
date: 2026-11-21
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
# ADX Filter for Keltner Channels and Retracement Entries

## Discovery Summary

E036-ADX-Based Indicator Selection states that rising ADX favors moving average-based indicators, while falling ADX favors oscillators. N190-Keltner Channels are a moving average-based volatility envelope, so their breakout and pullback signals are reliable only when ADX is rising. C050-Secondary Trend Retracement Range adds that secondary corrections typically retrace one-third to two-thirds of the prior move, allowing a trader to target entries within that zone using Keltner Channel levels during ADX-confirmed trends.

## Trading Implication

When ADX is rising, use Keltner Channel pullbacks near the 50% retracement zone to enter in the direction of the primary trend; when ADX is falling, ignore Keltner Channel signals and switch to oscillators.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-24-adx-filter-for-keltner-channel-pullback-entries|ADX filter for Keltner channel pullback entries]]
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
