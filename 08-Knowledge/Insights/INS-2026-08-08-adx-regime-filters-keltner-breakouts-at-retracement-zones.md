---
type: insight
date: 2026-08-08
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
# ADX Regime Filters Keltner Breakouts at Retracement Zones

## Discovery Summary

E036-adx-based-indicator-selection establishes that ADX rising favors MA-based indicators, while ADX falling favors oscillators. Keltner Channels (N190) are MA-based (EMA core with ATR bands), meaning their breakout signals are most reliable when ADX is rising. C050 adds a third layer: secondary trend retracements of 33-67% of the prior move represent high-probability zones where a breakout above/below Keltner Channels — confirmed by rising ADX — would signal trend resumption rather than a false breakout into ranging conditions.

## Trading Implication

Only take Keltner Channel breakout signals when ADX is rising AND price is within the 33-67% Fibonacci retracement zone of the prior swing, using the retracement level as a natural stop-loss anchor for the breakout trade.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
- [[INS-2026-08-17-adx-regime-filters-keltner-channel-breakout-signals-at-retra|ADX Regime Filters Keltner Channel Breakout Signals at Retracements]]
- [[INS-2026-08-01-adx-regime-filter-for-keltner-channel-breakout-validity|ADX Regime Filter for Keltner Channel Breakout Validity]]
