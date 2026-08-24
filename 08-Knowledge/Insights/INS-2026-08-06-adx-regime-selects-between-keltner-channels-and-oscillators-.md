---
type: insight
date: 2026-08-06
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
# ADX Regime Selects Between Keltner Channels and Oscillators at Retracements

## Discovery Summary

E036 establishes that rising ADX favors MA-based indicators while falling ADX favors oscillators. Keltner Channels (N190) are MA-based volatility envelopes — meaning they are most reliable when ADX is rising (trending). C050 identifies that secondary trend retracements of 1/3 to 2/3 of prior moves are high-probability decision points, but ADX typically falls during these corrections. This creates a specific sequencing rule: at a Dow retracement zone (33-66%), if ADX is falling, use oscillators to time re-entry into the primary trend rather than Keltner Channel breakouts, which would be unreliable in that low-ADX environment.

## Trading Implication

When price enters a secondary retracement zone (33-66% of prior primary trend move), check ADX direction: if falling, deploy oscillators to find re-entry; only use Keltner Channel breakout signals to confirm trend resumption once ADX turns upward again.

## Supporting Notes

- [[N190-keltner-channels]]
- [[E036-adx-based-indicator-selection]]
- [[C050-secondary-trend-retracement-range]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[C050-secondary-trend-retracement-range|Secondary Trend Retracement Range]]
- [[INS-2026-08-17-adx-regime-filters-keltner-channel-breakout-signals-at-retra|ADX Regime Filters Keltner Channel Breakout Signals at Retracements]]
