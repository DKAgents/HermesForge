---
type: insight
date: 2026-07-30
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume-Confirmed Breakout Filter with Stop Placement Logic

## Discovery Summary

N013 and N028 both establish that light-volume breakouts followed by heavy-volume declines signal false breakouts (bull traps). R052 provides a complementary set of structural filters (close-beyond-resistance, percentage penetration, two-day rule, Friday close) that, when combined with volume analysis from N013/N028, create a multi-condition confirmation system. The non-obvious connection is that R052's filters define the entry trigger threshold, while N013/N028's volume signature defines the exit/stop trigger: if a breakout passes R052's structural filters but then shows heavy-volume reversal, the stop should be placed just below the breakout level (the prior resistance peak now acting as failed support), since the bull trap pattern in N028 implies a sharp reversal follows.

## Trading Implication

A trader should only enter on breakouts that satisfy at least one structural filter from R052 (e.g., two consecutive closes above resistance) AND show above-average volume; if volume is light on the breakout, place a tight stop just below the breakout level and watch for heavy-volume reversal as the exit signal confirming a bull trap.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
