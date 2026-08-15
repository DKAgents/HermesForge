---
type: insight
date: 2026-08-15
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Regime Gates Keltner Channel Breakout vs Retracement Entries

## Discovery Summary

E036 establishes that ADX rising favors MA-based indicators while ADX falling favors oscillators. Keltner Channels (N190) are MA-based (EMA + ATR bands), meaning they are most reliable as breakout tools when ADX is rising. When ADX is falling, C050's Dow retracement framework (33%-67%, most commonly 50%) becomes the preferred entry model, replacing Keltner breakout signals with fade-the-band mean-reversion entries aligned to secondary trend correction targets.

## Trading Implication

When ADX is rising, trade Keltner Channel breakouts in the direction of the primary trend; when ADX is falling, switch to fading Keltner Channel extremes and target 50% retracement entries per Dow's secondary trend correction range instead of seeking new breakouts.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
