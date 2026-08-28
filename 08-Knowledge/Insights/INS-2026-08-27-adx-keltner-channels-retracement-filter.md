---
type: insight
date: 2026-08-27
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
# ADX + Keltner Channels + Retracement Filter

## Discovery Summary

E036 states that moving average-based indicators are preferred when ADX is rising, and N190 Keltner Channels are volatility envelopes around an EMA, making them MA-based. C050 specifies that secondary trends retrace 33–66% of the prior move. In a rising ADX regime, after a pullback to the retracement zone, a Keltner Channel breakout in the primary trend’s direction confirms a filtered entry.

## Trading Implication

Only take Keltner Channel breakouts when ADX is rising, and time entries after a secondary trend retraces to the 33–66% range of the prior impulse, ideally near the 50% level, to improve trend-continuation odds.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5
