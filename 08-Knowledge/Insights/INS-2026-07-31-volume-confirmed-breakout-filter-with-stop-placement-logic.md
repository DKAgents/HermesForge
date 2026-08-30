---
type: insight
date: 2026-07-31
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
# Volume-Confirmed Breakout Filter with Stop Placement Logic

## Discovery Summary

N013 and N028 together establish that a valid breakout requires heavy volume on the upside move, while a bull trap (N028) is characterized by light-volume breakout followed by heavy-volume decline. R052 provides a multi-layered confirmation framework (close-based filters, percentage criteria, two-day rule, Friday close) that, when combined with the volume signal from N013/N028, creates a composite decision rule: a breakout is only acted upon when it satisfies at least one price-based filter from R052 AND is accompanied by heavy volume. The seed question's stop placement implication emerges from N028: if a breakout occurs on light volume, a subsequent heavy-volume decline signals the trap has been sprung, and the stop should be placed just below the breakout level (the prior resistance now acting as failed support).

## Trading Implication

A trader should only enter a long breakout when both a price filter (e.g., 2-day close above resistance per R052) AND heavy volume are confirmed; if a breakout occurs on light volume, place a tight stop just below the breakout level and exit immediately on the first heavy-volume down day, which per N028 confirms a bull trap.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]] — See foundational volume rule for breakouts
