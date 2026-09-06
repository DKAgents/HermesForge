---
type: insight
date: 2026-09-06
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
---

# ADX Filters Keltner Channels with Dow Retracements

## Discovery Summary

E036 states that a rising ADX favors moving average-based indicators. Keltner Channels (N190) are EMA-based with ATR bands, thus a valid tool during trending regimes. C050 specifies that corrections in a primary trend typically retrace one-third to two-thirds. By combining these, ADX rising acts as a filter to validate Keltner Channel trend signals, while Dow retracement levels (33-66%) offer precise entry zones within that trend for pullback trades.

## Trading Implication

Only act on Keltner Channel breakouts or band touches when ADX is rising; enter long near the lower band or on pullbacks that retrace 33-66% of the prior upswing, placing stops below the 66% retracement or the opposite channel band.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5
