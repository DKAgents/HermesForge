---
type: insight
date: 2026-08-22
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
# Volume-Confirmed False Breakout Stop Placement System

## Discovery Summary

N013 and N028 together establish that a bull trap signature has two sequential volume components: light volume on the upside breakout followed by heavy volume on the subsequent decline. R052 provides five confirmation filters for valid breakouts, including the two-day close rule and percentage penetration criteria. The non-obvious connection is that these filters, when FAILING (i.e., breakout does not achieve a 1-3% penetration, does not hold for two consecutive closes, and shows the N013/N028 volume inversion pattern), collectively define a precise entry trigger for a short position with a clear stop-loss level: the false breakout high itself.

## Trading Implication

When an upside breakout fails R052's close-based and percentage filters AND shows light-volume advance followed by heavy-volume reversal per N013/N028, enter short on the heavy-volume reversal day with a stop placed just above the false breakout high, treating that level as the invalidation point.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
