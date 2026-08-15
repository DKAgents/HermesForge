---
type: insight
date: 2026-08-14
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
# Volume-Confirmed Breakout Failure as Stop Placement Signal

## Discovery Summary

N013 and N028 together establish a two-stage volume signature for false breakouts: light volume on the upside break followed by heavy volume on the subsequent decline. R052 provides the pre-breakout confirmation filters (close beyond resistance, percentage criterion, two-day rule) that must FIRST be satisfied before the volume test is applied. The non-obvious connection is that when a breakout passes R052's price-based filters but fails N013's volume test, it creates a high-conviction short setup — the filters reduce random noise while the volume divergence identifies the specific bull-trap pattern described in N028.

## Trading Implication

A trader should wait for a breakout that clears R052's price filters (e.g., 2-day close above resistance), then monitor volume: if breakout volume is light AND a subsequent decline occurs on heavy volume, initiate a short position with a stop placed just above the false breakout high, as that level now acts as confirmed resistance.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
