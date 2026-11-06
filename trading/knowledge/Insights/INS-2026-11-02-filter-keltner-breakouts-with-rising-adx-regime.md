---
type: insight
date: 2026-11-02
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Filter Keltner Breakouts with Rising ADX Regime

## Discovery Summary

E036 ADX-Based Indicator Selection states that moving-average-based indicators are preferred when ADX is rising, while oscillators are preferred when ADX is falling. Keltner Channels are built on an EMA and ATR, making them a moving-average-based trend/breakout tool. Therefore ADX regime detection should filter Keltner signals: only act on Keltner breakouts when ADX is rising. In that trending context, C050 Secondary Trend Retracement Range adds that pullbacks typically retrace one-third to two-thirds of the prior move, helping frame entries within the trend.

## Trading Implication

Use rising ADX as a regime filter before taking Keltner Channel breakout signals; when ADX is falling, switch to oscillator-based signals. Within rising-ADX trends, expect secondary pullbacks to retrace roughly one-third to two-thirds of the prior move before the trend resumes.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
