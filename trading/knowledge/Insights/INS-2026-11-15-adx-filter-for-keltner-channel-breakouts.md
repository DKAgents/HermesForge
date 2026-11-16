---
type: insight
date: 2026-11-15
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
# ADX Filter for Keltner Channel Breakouts

## Discovery Summary

E036 states that moving-average-based indicators are preferred when ADX is rising, while oscillators are preferred when ADX is falling. Keltner Channels are constructed from an EMA with ATR bands, making them a moving-average-based indicator. Therefore, ADX regime acts as a filter: rising ADX confirms the reliability of Keltner Channel breakout signals, while falling ADX indicates ranging conditions where they are prone to false signals.

## Trading Implication

Trade Keltner Channel breakouts only when ADX is rising, and avoid them when ADX is falling in favor of oscillator-based signals. This prevents whipsaw losses in non-trending markets.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5
