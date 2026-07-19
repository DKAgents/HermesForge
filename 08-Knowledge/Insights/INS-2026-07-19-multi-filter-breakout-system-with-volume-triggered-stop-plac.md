---
type: insight
date: 2026-07-19
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Multi-Filter Breakout System with Volume-Triggered Stop Placement

## Discovery Summary

R052 provides structural confirmation filters (close-beyond, percentage rule, two-day rule, Friday close) while N013 and N028 together establish volume as a directional qualifier: a breakout on light volume followed by a heavy-volume decline is the specific signature of a bull trap (N028). Combining these, a trader can construct a layered decision rule: a breakout must first pass at least one structural filter from R052 before volume is examined, and if volume fails the N013 test (light on breakout, heavy on reversal), the position should be exited or a short initiated. The seed question adds the missing stop-placement dimension — the bull trap high (N028) becomes the logical stop reference for any resulting short trade, since price reclaiming that level invalidates the false-breakout thesis.

## Trading Implication

A trader should require both a structural filter from R052 (e.g., two consecutive closes above resistance) AND confirming volume before entering a breakout long; if volume is light on the breakout and subsequently heavy on a reversal, treat the breakout high as a bull trap (N028) and place a buy-stop just above that high when entering a counter-trend short.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
