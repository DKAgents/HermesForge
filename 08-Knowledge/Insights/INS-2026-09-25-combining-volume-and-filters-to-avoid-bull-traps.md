---
type: insight
date: 2026-09-25
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Combining volume and filters to avoid bull traps

## Discovery Summary

N013's volume filter (light volume breakout then heavy volume decline) combined with R052's confirmation criteria (close beyond resistance, percentage penetration) helps identify N028's bull traps early. This sequence reveals that a breakout failing both volume and price confirmation is likely a false breakout, allowing traders to set stops accordingly.

## Trading Implication

When a breakout occurs on light volume and fails to close beyond resistance or meet percentage criteria, treat it as a potential bull trap. Either avoid entering or place a stop loss just below the breakout level to capture the reversal.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**adds_condition** — Actionability score: 4/5
