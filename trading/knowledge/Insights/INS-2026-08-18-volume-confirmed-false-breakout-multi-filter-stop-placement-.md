---
type: insight
date: 2026-08-18
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
# Volume-Confirmed False Breakout: Multi-Filter Stop Placement System

## Discovery Summary

N013 and N028 together establish a two-signal false breakout detection sequence: light volume on the initial breakout followed by heavy volume on the subsequent decline. R052 provides the complementary entry confirmation filters (close beyond resistance, percentage penetration, two-day rule) that precede this sequence. The non-obvious connection is that R052's filters define the conditions under which a breakout is initially accepted as valid, while N013/N028's volume reversal signals define the precise moment that accepted breakout should be treated as a bull trap — creating a two-stage decision framework with a natural stop placement trigger: exit when heavy-volume decline follows the light-volume breakout.

## Trading Implication

A trader should first require a confirmed breakout per R052's filters (close beyond resistance, ideally on Friday), then monitor volume on any subsequent decline — if that decline arrives on heavy volume after a light-volume breakout, treat the position as a bull trap and exit immediately, placing stops just below the breakout level as the trigger.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
