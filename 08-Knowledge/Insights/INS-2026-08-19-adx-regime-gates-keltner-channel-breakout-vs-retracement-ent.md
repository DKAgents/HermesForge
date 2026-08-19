---
type: insight
date: 2026-08-19
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Regime Gates Keltner Channel Breakout vs Retracement Entries

## Discovery Summary

E036 establishes that ADX direction determines indicator class suitability: rising ADX favors MA-based tools, falling ADX favors oscillators. Keltner Channels (N190) are MA-based (EMA core with ATR bands), making them most reliable during rising ADX trending regimes. C050 adds that secondary corrections retrace 33-67% of prior moves, meaning during falling ADX (ranging/corrective phase), a trader should expect price to mean-revert within Keltner bands rather than break out through them.

## Trading Implication

When ADX is rising, trade Keltner Channel breakouts as trend continuation signals; when ADX is falling, fade touches of the outer Keltner bands expecting a 50% Fibonacci retracement back toward the EMA centerline.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5
