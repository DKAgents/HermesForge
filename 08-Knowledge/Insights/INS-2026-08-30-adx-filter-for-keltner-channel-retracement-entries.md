---
type: insight
date: 2026-08-30
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
# ADX Filter for Keltner Channel Retracement Entries

## Discovery Summary

E036 states that when ADX is rising (trending market), moving average-based indicators are preferred. N190 describes Keltner Channels as EMA-based envelopes with ATR bands, making them an MA indicator. C050 notes that secondary trend corrections typically retrace 1/3 to 2/3, often 50%. Combined, a rising ADX validates the trend, allowing a trader to use Keltner Channel bands as dynamic entry zones during pullbacks that approximate the 50% retracement level, filtering out trades when ADX is falling and the channels are prone to whipsaw.

## Trading Implication

Use ADX rising as a precondition: only take Keltner Channel band touch or breakout signals when ADX confirms a trending regime. During an uptrend, consider long entries at the lower Keltner band when price retraces toward the common 50% level of the prior move, avoiding those signals if ADX is flat or falling.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5
