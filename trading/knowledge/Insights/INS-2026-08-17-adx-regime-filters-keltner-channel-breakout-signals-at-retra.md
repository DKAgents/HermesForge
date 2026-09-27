---
type: insight
date: 2026-08-17
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
# ADX Regime Filters Keltner Channel Breakout Signals at Retracements

## Discovery Summary

E036-adx-based-indicator-selection establishes that ADX rising (trending) favors MA-based indicators while ADX falling (ranging) favors oscillators. Keltner Channels (N190) are MA+ATR envelopes, making them MA-based — therefore most reliable when ADX is rising. C050 identifies that secondary corrections retrace 33-67% of prior trend moves, creating predictable zones where price re-tests Keltner Channel midlines (the EMA) during pullbacks. Combining these: a Keltner Channel bounce from the midline EMA during a retracement of 33-67% is only a high-confidence re-entry if ADX is simultaneously rising (confirming the primary trend is intact).

## Trading Implication

Only take Keltner Channel midline-bounce entries during 33-67% retracements when ADX is rising; if ADX is falling during the retracement, switch to an oscillator for timing the re-entry instead of relying on the Keltner midline.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[INS-2026-08-01-adx-regime-filter-for-keltner-channel-breakout-validity|ADX Regime Filter for Keltner Channel Breakout Validity]]
