---
type: insight
date: 2026-09-23
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# ADX Filters Keltner Channels for Trending Reliability

## Discovery Summary

E036-ADX-Based Indicator Selection states that when ADX is rising, MA-based indicators are preferred, while oscillators suit falling ADX. N190-Keltner Channels are volatility bands built on an EMA and ATR, making them MA-based/trend-following. C050-Secondary Trend Retracement Range quantifies corrections as typically retracing 1/3 to 2/3 of the prior move, which can be used as a target zone within a Keltner-driven trend trade. The non-obvious connection is that Keltner Channel trading signals (e.g., price hugging upper band) should only be trusted when ADX confirms a trending regime; otherwise, the same setups likely fail in ranges.

## Trading Implication

Before acting on Keltner Channel breakouts or trend continuation signals, check the ADX slope: only take long signals when ADX is rising (indicating trend), and avoid counter-trend Keltner-based mean reversion except when ADX is falling. Additionally, use the 1/3–2/3 retracement range from Dow theory as a potential profit target or re-entry zone within the trend.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
