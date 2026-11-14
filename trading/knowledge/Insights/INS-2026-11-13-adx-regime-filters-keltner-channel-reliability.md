---
type: insight
date: 2026-11-13
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

E036 ADX-Based Indicator Selection states that MA-based indicators are preferred when ADX is rising, while oscillators are preferred when ADX is falling. Keltner Channels are MA/ATR-based envelopes, so their signals inherit this regime dependency. C050 Secondary Trend Retracement Range adds that in a valid trend, pullbacks typically retrace one-third to two-thirds of the prior move, commonly near 50%, giving a structured entry zone once the ADX regime supports trend-following tools.

## Trading Implication

Check ADX slope before acting on Keltner/MA signals: when ADX is rising, use Keltner/MA signals in the trend direction and time entries near the 1/3–2/3 retracement zone. When ADX is falling, avoid Keltner/MA crossover signals and switch to oscillator-based signals.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5
