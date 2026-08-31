---
type: insight
date: 2026-08-31
actionability: 3
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume-Confirmed Stop Placement on False Breakouts

## Discovery Summary

Volume as a Filter for False Breakouts (N013) warns that light-volume upside breakouts often fail, and a subsequent heavy-volume decline confirms a bull trap (N028). Filters for Confirming Breakouts (R052) adds the requirement of a close beyond the previous peak for two consecutive days. Combining these: if an upside breakout occurs on light volume and fails to close above the resistance peak for two straight days, it flags a likely false breakout. Place a stop loss at the low of the breakout day to exit quickly when the reversal begins.

## Trading Implication

If an upside breakout lacks above-average volume and does not achieve two consecutive closes above the prior resistance peak, treat it as a potential bull trap and set a stop-loss order just below the breakout day's low.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 3/5
