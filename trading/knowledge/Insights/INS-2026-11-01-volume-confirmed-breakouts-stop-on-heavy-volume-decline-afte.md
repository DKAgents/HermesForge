---
type: insight
date: 2026-11-01
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, trading_rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume-Confirmed Breakouts: Stop on Heavy-Volume Decline After Light-Volume Breakout

## Discovery Summary

N013 and N028 establish a bearish sequence: an upside breakout on light volume followed by a decline on heavy volume identifies the breakout as a likely bull trap. R052 provides price-based confirmation filters but omits the volume condition. Adding the volume filter from N013 to R052's filters means a breakout that satisfies price criteria but occurs on light volume is suspect; the subsequent heavy-volume decline is the trigger to exit longs or place stops rather than waiting for a deeper price move.

## Trading Implication

Traders should only enter breakouts accompanied by heavy volume, and if already long after a light-volume breakout, exit immediately when a decline occurs on heavy volume instead of relying on wider stops.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**adds_condition** — Actionability score: 4/5
