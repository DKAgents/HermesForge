---
type: insight
date: 2026-09-11
actionability: 4
connection_type: creates_filter
domains: [concepts, edge-conditions, indicators]
sources: ["N190-keltner-channels", "E036-adx-based-indicator-selection", "C050-secondary-trend-retracement-range"]
seed_id: ma_crossover_adx_regime
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# ADX Regime + Retracement + Keltner Entry

## Discovery Summary

E036 states that a rising ADX favors moving average-based indicators. N190 Keltner Channels are EMA-based volatility envelopes suited for trending markets. C050 shows secondary trends typically retrace 33–66% of the prior move. By combining these, a trader can filter entries to periods when ADX is rising, wait for a pullback into the retracement zone, and trigger on a Keltner Channel breakout in the primary trend direction, aligning regime detection, retracement theory, and volatility breakout signals.

## Trading Implication

Only consider trades when ADX is rising; on a pullback to roughly 50% of the prior impulse, enter on a close beyond the Keltner band in the trend direction. In downtrends, reverse the logic.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5
