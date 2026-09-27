---
type: insight
date: 2026-08-23
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
# Volume-Confirmed Breakout Failure: Multi-Filter Stop Placement System

## Discovery Summary

N013 and N028 jointly establish that a false breakout (bull trap) has a specific two-part volume signature: light volume on the upside break followed by heavy volume on the subsequent decline. R052 provides five confirmatory filters that must be satisfied for a breakout to be considered valid, including close-basis confirmation, percentage penetration, and two-day rules. The non-obvious connection is that these filters from R052 can be inverted to define a high-confidence false breakout scenario: if a breakout fails R052's filters (e.g., only intraday penetration, no volume confirmation) AND then shows the heavy-volume decline pattern from N013/N028, traders have a multi-layered signal to act on the short side with defined entry logic.

## Trading Implication

When a price breaks above resistance on light volume without satisfying R052's close-basis or two-day confirmation filters, treat it as a suspected bull trap; if the subsequent session shows heavy volume decline back below the breakout level, initiate or add to a short position with a stop placed just above the failed breakout high.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
