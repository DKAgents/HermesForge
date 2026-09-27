---
type: insight
date: 2026-08-19
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
# Volume-Confirmed Breakout Failure: Filter Stack + Stop Placement

## Discovery Summary

N013 and N028 together establish a two-signal confirmation that a breakout is false: light volume on the initial upside break followed by heavy volume on the subsequent decline. R052 provides a complementary set of price-based filters (close-beyond-resistance, percentage penetration, two-day rule, Friday close) that, when combined with N013's volume filter, create a multi-layered false breakout detection system. The seed question adds the missing operational step: once the bull trap pattern from N028 is confirmed by volume divergence per N013, stops for long positions should be placed just below the breakout level that failed to hold on volume, converting the pattern recognition into a specific risk management rule.

## Trading Implication

When a breakout meets fewer than two of R052's price filters AND occurs on light volume (N013), treat any subsequent heavy-volume decline as confirmation of a bull trap (N028) and exit longs immediately with stops placed just below the failed breakout level.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
