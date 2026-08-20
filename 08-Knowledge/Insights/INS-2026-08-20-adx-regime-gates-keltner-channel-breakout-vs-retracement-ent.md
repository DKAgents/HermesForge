---
type: insight
date: 2026-08-20
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Regime Gates Keltner Channel Breakout vs. Retracement Entries

## Discovery Summary

E036-adx-based-indicator-selection establishes that rising ADX favors MA-based indicators while falling ADX favors oscillators. Keltner Channels (N190-keltner-channels) are MA-based (EMA core with ATR bands), making them most reliable when ADX is rising. When ADX is falling, C050-secondary-trend-retracement-range provides a complementary framework: expect 33-67% retracements of prior moves rather than breakouts, making oscillator-timed entries at Fibonacci/Dow retracement levels the preferred tactic instead of Keltner band breakouts.

## Trading Implication

When ADX is rising, trade Keltner Channel breakouts in the trend direction; when ADX is falling, abandon Keltner breakout signals and instead fade moves toward the 50% retracement of the prior swing using an oscillator confirmation entry.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5
