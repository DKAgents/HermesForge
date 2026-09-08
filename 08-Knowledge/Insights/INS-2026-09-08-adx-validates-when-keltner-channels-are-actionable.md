---
type: insight
date: 2026-09-08
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX validates when Keltner Channels are actionable

## Discovery Summary

ADX-based indicator selection (E036) states that when ADX is rising, moving average-based indicators are preferred. Keltner Channels (N190) are built on an exponential moving average with ATR-based envelopes, making them an MA-based tool. When ADX is rising and the secondary trend retracement range (C050) shows a pullback of one-third to two-thirds of the prior move, a trader can use Keltner Channel band touches during that retracement as high-probability entry points, but only if ADX confirms the trending regime — without ADX confirmation, the same Keltner Channel signal during a ranging market would be unreliable.

## Trading Implication

Before entering on a Keltner Channel breakout or pullback-to-band signal, check that ADX is rising. If ADX is flat or falling, ignore Keltner Channel signals entirely and switch to oscillators per E036.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
