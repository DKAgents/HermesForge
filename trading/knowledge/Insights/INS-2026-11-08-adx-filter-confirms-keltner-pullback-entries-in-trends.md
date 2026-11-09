---
type: insight
date: 2026-11-08
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
# ADX Filter Confirms Keltner Pullback Entries in Trends

## Discovery Summary

In trending markets (ADX rising), MA-based indicators like Keltner Channels are preferred per 'ADX-Based Indicator Selection'. Keltner Channels use an EMA and ATR to define volatility envelopes, so pullbacks within a trend can be traded at the lower band. The 'Secondary Trend Retracement Range' note adds that corrections typically retrace 1/3 to 2/3 of the prior move, commonly 50%. Combining these, an ADX filter confirms when a Keltner Channel touch is a valid trend pullback rather than a range-bound oscillation.

## Trading Implication

Only take long Keltner Channel lower-band entries in an uptrend when ADX is rising, and require the pullback to be within the 1/3–2/3 retracement zone of the prior swing; avoid entries when ADX is falling.

## Supporting Notes

- [[N190-keltner-channels]]
- [[C050-secondary-trend-retracement-range]]
- [[E036-adx-based-indicator-selection]]

## Connection Type

**creates_filter** — Actionability score: 4/5
