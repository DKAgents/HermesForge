---
type: insight
date: 2026-09-17
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
# ADX Gating for Keltner Channel and Retracement Signals

## Discovery Summary

Keltner Channels provide volatility-based entry points around an EMA, but their signals are only reliable in trending conditions. ADX-Based Indicator Selection indicates that when ADX is rising (trending), moving average-based tools like Keltner Channels should be preferred; when ADX is falling (ranging), oscillators are better. Additionally, Secondary Trend Retracement Range suggests that in a secondary correction, price often retraces 50% of the prior move, which could align with a Keltner band touch during an uptrend. The non-obvious connection is that a rising ADX can serve as a confirmation filter for Keltner band touch or retracement entries, avoiding false signals in ranging markets.

## Trading Implication

A trader should enter long on a Keltner Channel lower-band touch or a 50% retracement pullback only when ADX is rising (preferably above 20), and switch to oscillator-based strategies or stand aside when ADX is falling to avoid whipsaws.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
