---
type: insight
date: 2026-08-23
actionability: 4
connection_type: adds_condition
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Regime Gates Keltner Channel Breakout Reliability at Retracements

## Discovery Summary

E036 establishes that ADX distinguishes trending vs ranging regimes, determining whether MA-based or oscillator indicators are appropriate. N190 describes Keltner Channels as MA-based volatility envelopes used for breakout identification. C050 defines secondary trend retracements as occurring within the 33%-67% zone. The non-obvious synthesis: when price retraces into the 1/3–2/3 Fibonacci zone (C050), use ADX to determine whether Keltner Channel breakouts from that retracement zone are trustworthy — only enter on Keltner Channel breakouts during rising ADX, and treat Keltner Channel touches as mean-reversion signals during falling ADX.

## Trading Implication

When price pulls back into the 33%-67% retracement zone of the prior swing, check ADX direction: if ADX is rising, trade a Keltner Channel upper-band breakout as a trend continuation entry; if ADX is falling, fade the channel band as a range-bound mean-reversion trade instead.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5
