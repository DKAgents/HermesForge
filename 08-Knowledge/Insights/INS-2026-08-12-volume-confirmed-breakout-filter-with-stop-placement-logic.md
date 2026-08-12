---
type: insight
date: 2026-08-12
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume-Confirmed Breakout Filter With Stop Placement Logic

## Discovery Summary

N013 and N028 together establish that a valid breakout requires heavy volume on the upside move, while a light-volume breakout followed by heavy-volume decline signals a bull trap. R052 adds structural confirmation filters (close beyond resistance, 1-3% penetration, two-day rule, Friday close) that, when combined with the volume signal from N013/N028, create a multi-condition entry gate. The non-obvious connection is that these filters can also define stop placement: if price closes back below the breakout level on heavy volume after a light-volume penetration, that is the precise exit trigger implied by N028's 'negative chart combination.'

## Trading Implication

A trader should only enter a breakout when both structural filters from R052 (e.g., 2-day close beyond resistance) AND heavy volume from N013 are satisfied simultaneously; if a breakout occurs on light volume, place a tight stop just below the breakout level and exit immediately if a subsequent heavy-volume decline materializes as described in N028.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
