---
type: insight
date: 2026-08-20
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Multi-Filter Breakout System With Volume-Based Stop Logic

## Discovery Summary

R052 provides a menu of breakout confirmation filters (close-beyond, percentage penetration, two-day rule, Friday close, volume) while N013 and N028 together specify the exact volume signature that marks a breakout as false: light volume on the initial break followed by heavy volume on the subsequent decline. The non-obvious connection is that these three notes together define not just an entry filter but also a stop-placement trigger: once the bull trap signature (light-volume breakout + heavy-volume reversal) is confirmed, the trader has a specific, observable two-bar sequence that validates an exit or short entry rather than waiting for a percentage stop to be hit.

## Trading Implication

A trader should require at least two of R052's confirmation filters before entering a breakout, and immediately exit or reverse short if the subsequent bar shows heavy volume declining — treating that two-bar volume sequence from N013/N028 as the hard stop signal rather than a fixed price level.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
