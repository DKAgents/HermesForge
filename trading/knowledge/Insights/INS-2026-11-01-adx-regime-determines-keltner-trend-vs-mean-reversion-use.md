---
type: insight
date: 2026-11-01
actionability: 4
connection_type: creates_filter
domains: [indicators, market-structure, regime-detection, retracement-theory]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# ADX Regime Determines Keltner Trend vs. Mean-Reversion Use

## Discovery Summary

E036 ADX-Based Indicator Selection states that when ADX is rising, moving average-based indicators are preferred, and Keltner Channels are built on an exponential moving average. This makes ADX slope a filter for how to interpret Keltner Channels: in trending regimes, use them for trend continuation, while in falling-ADX ranging regimes, treat band touches as oscillator extremes. C050 Secondary Trend Retracement Range adds that secondary corrections typically retrace one-third to two-thirds of the prior move, with 50% most common, supplying a defined entry zone for Keltner/MA pullback trades.

## Trading Implication

Check ADX slope first: if ADX is rising, enter on pullbacks to the Keltner middle/lower band that fall within the 1/3-to-2/3 retracement zone of the prior move; if ADX is falling, stop using Keltner breakout signals and instead fade band touches or switch to an oscillator.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
