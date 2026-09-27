---
type: insight
date: 2026-08-09
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
# Multi-Filter False Breakout Detection With Stop Placement Logic

## Discovery Summary

N013 and N028 together establish that a light-volume upside breakout followed by heavy-volume decline is the signature of a bull trap. R052 provides the mechanical confirmation filters (close-beyond rule, percentage penetration, two-day rule, Friday close) that must be applied before treating any breakout as valid. The non-obvious connection is that R052's filters and N013's volume condition operate as a stacked, sequential filter system: if a breakout fails the volume test (N013/N028), the trader should NOT apply the percentage or time-based filters at all — the volume failure alone is sufficient to treat the breakout as suspect and set a stop just above the false breakout high.

## Trading Implication

When an upside breakout occurs on light volume, a trader should immediately treat it as a potential bull trap, place a stop just above the breakout high (to limit loss if price briefly pushes higher), and watch for any subsequent heavy-volume decline as the trigger to exit or initiate a short position rather than waiting for the R052 confirmation filters to be satisfied.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
