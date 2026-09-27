---
type: insight
date: 2026-08-17
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume-Gated Breakout Filter With Stop Placement Protocol

## Discovery Summary

N013 and N028 establish that false breakouts (bull traps) are characterized by light volume on the upside break followed by heavy volume on the subsequent decline. R052 provides a menu of confirmation filters (close-based, percentage, two-day, Friday close, volume) that can be layered together. The non-obvious connection is that these filters can be sequenced as a tiered decision gate: first apply a close-based or two-day penetration rule from R052 to reduce intraday noise, then use the volume signature from N013/N028 as a second-stage filter — requiring heavy volume on the breakout candle itself and treating any post-breakout heavy-volume reversal as an immediate invalidation signal.

## Trading Implication

A trader should only enter on a breakout that clears both a structural filter (close above prior resistance, ideally on two consecutive days or a Friday close per R052) AND shows heavy volume; if volume is light on the breakout, either skip the trade or set a tight stop just below the breakout level and exit immediately on any subsequent heavy-volume reversal candle.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
