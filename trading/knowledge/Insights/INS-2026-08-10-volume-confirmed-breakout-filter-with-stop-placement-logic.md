---
type: insight
date: 2026-08-10
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

N013 and N028 together establish that light-volume breakouts followed by heavy-volume declines are the defining signature of a bull trap (false upside breakout). R052 provides a layered confirmation framework — requiring a close beyond resistance, a percentage filter, and two-day rule — that, combined with volume analysis from N013/N028, creates a multi-condition entry gate. The non-obvious connection is that R052's filters can be sequenced: first apply the close-based and percentage filters to identify candidate breakouts, then apply the volume condition from N013 as a final gate, and use the light-volume/heavy-decline pattern from N028 as a stop-trigger signal rather than a static price stop.

## Trading Implication

A trader should enter a breakout only when it satisfies at least two of R052's price-based filters AND shows heavy volume on the breakout day; if a breakout passes price filters but occurs on light volume, place a tight stop just below the breakout level and treat a subsequent heavy-volume down day as an immediate exit signal confirming the bull trap.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
