---
type: insight
date: 2026-08-08
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
# Multi-Filter False Breakout Detection With Volume-Based Stop Placement

## Discovery Summary

N013 and N028 establish that a light-volume upside breakout followed by a heavy-volume decline is a reliable bull trap signature, while R052 provides complementary non-volume filters (close-basis confirmation, percentage penetration, two-day rule, Friday close) to validate breakouts before entry. The non-obvious connection is that these filters can be layered sequentially: first apply R052's close-basis and percentage filters to decide whether to enter, then use N013/N028's volume signature as an early exit trigger if the breakout was entered. Specifically, if a trader enters on a breakout that passed R052's filters but subsequently observes declining follow-through volume with a heavy-volume reversal day, N028's bull trap pattern provides the stop-exit signal not captured by the initial entry filters alone.

## Trading Implication

A trader should enter breakouts only when R052's close-basis and percentage filters are satisfied, but immediately exit the position (or place a stop just below the breakout level) if post-entry volume shows the light-volume breakout / heavy-volume reversal pattern described in N013 and N028, treating that volume signature as a confirming bull trap trigger.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
