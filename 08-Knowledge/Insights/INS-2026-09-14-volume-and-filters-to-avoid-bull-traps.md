---
type: insight
date: 2026-09-14
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, trading rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume and Filters to Avoid Bull Traps

## Discovery Summary

Combine the volume filter from N013 with the confirmation filters from R052 to identify bull traps (N028). A valid breakout requires heavy volume and a close beyond resistance; a false breakout shows light volume on the breakout followed by a heavy volume decline. This integrated filter provides a clear rule to avoid false breakouts.

## Trading Implication

Only enter a breakout if volume is heavy and price closes beyond resistance; if already in a breakout that later shows light volume followed by heavy decline, exit immediately to avoid a bull trap.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
