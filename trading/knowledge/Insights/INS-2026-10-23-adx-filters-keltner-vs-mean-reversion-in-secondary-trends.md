---
type: insight
date: 2026-10-23
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# ADX Filters Keltner vs Mean Reversion in Secondary Trends

## Discovery Summary

E036 states ADX should drive indicator selection based on trend strength. N190 Keltner Channels provide volatility-based bands whose middle line is a moving average, making them mean-reverting in ranges but trend-following on breakouts. C050 defines retracement ranges for secondary trends, giving entry levels after pullbacks. The non-obvious link is that high ADX makes Keltner breakouts and MA crossovers reliable for trend continuation, while low ADX favors fading reversion to the middle band; C050 then supplies the pullback zone for entries.

## Trading Implication

Use ADX to switch modes: with ADX above threshold, trade Keltner breakouts aligned with secondary trend retracements; with ADX below threshold, fade moves back to the Keltner middle band using C050 range levels.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
