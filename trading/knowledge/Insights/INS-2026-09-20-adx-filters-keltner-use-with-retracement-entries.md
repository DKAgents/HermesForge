---
type: insight
date: 2026-09-20
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
# ADX filters Keltner use with retracement entries

## Discovery Summary

ADX-Based Indicator Selection (E036) states that rising ADX favors MA-based indicators like Keltner Channels (N190). Secondary Trend Retracement Range (C050) adds that corrections retrace 33-66% of prior move. Together, in a rising ADX regime, Keltner Channels can identify trends, and pullbacks to the EMA or band edges that match retracement levels offer high-probability entries.

## Trading Implication

Only trade Keltner Channel breakouts or bounce entries when ADX is rising, and use the 33-66% retracement zone (especially 50%) to time entries on pullbacks.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[INS-2026-09-07-adx-filters-keltner-channel-breakouts-by-trend-validity|ADX filters Keltner Channel breakouts by trend validity]]
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
