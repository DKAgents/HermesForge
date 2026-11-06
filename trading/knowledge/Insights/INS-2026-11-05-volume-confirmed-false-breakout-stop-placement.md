---
type: insight
date: 2026-11-05
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, risk_management, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume-Confirmed False Breakout Stop Placement

## Discovery Summary

The combination of N013 (volume as filter for false breakouts) and N028 (bull trap) establishes a specific negative chart combination: an upside breakout on light volume followed by a decline on heavy volume signals a false breakout. R052 (filters for confirming breakouts) recommends examining volume on the breakout. Together, they imply that when this volume pattern appears, a trader should treat the breakout as invalid and place stops accordingly—either exiting long positions or initiating shorts below the breakout level.

## Trading Implication

On any upside breakout, require heavy volume for confirmation; if the breakout occurs on light volume and is followed by a heavy-volume decline, immediately place a stop-loss below the recent swing low or exit long positions to avoid the bull trap.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**adds_condition** — Actionability score: 4/5
