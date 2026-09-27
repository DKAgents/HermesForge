---
type: insight
date: 2026-08-07
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
# Volume-Confirmed Breakout Filter With Stop Placement Logic

## Discovery Summary

N013 and N028 together establish that a valid breakout requires heavy volume on the upside move, and that light-volume breakouts followed by heavy-volume declines are negative combinations signaling bull traps. R052 provides the structural confirmation filters (close beyond resistance, percentage criterion, two-day rule, Friday close) that must be satisfied before volume is even evaluated. The three-way connection reveals a sequenced decision rule: first apply R052's price-based filters to establish a candidate breakout, then use N013/N028's volume condition as a final gate — and critically, the bull trap pattern in N028 implies that a stop should be placed just below the breakout level, since a heavy-volume reversal after a light-volume breakout signals rapid failure.

## Trading Implication

A trader should only enter on breakouts that satisfy at least one price filter from R052 (e.g., close beyond resistance) AND confirm with heavy volume; if volume is light on the breakout, place a tight stop just below the breakout level or avoid the trade entirely, as N028 warns the subsequent decline is likely to be heavy-volume and swift.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
