---
type: insight
date: 2026-08-16
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
# Multi-Filter Stop Placement on False Breakout Detection

## Discovery Summary

N013 and N028 both establish that light-volume breakouts followed by heavy-volume declines signal false breakouts (bull traps). R052 provides a complementary set of confirmation filters (close-based, percentage-based, two-day rule, Friday close) that, when combined with the volume signature from N013/N028, create a stacked filter system. The non-obvious connection is that R052's filters define ENTRY confirmation thresholds, while N013/N028's volume divergence pattern defines the EXIT/stop trigger — together they form a complete entry-and-invalidation framework rather than just a breakout confirmation checklist.

## Trading Implication

A trader should enter a breakout only after it passes at least one R052 structural filter (e.g., two consecutive closes above resistance) AND is accompanied by heavy volume; if price subsequently declines on heavy volume after a light-volume breakout, treat that as an immediate stop-and-reverse signal rather than waiting for a standard price-based stop to be hit.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
