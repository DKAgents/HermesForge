---
type: insight
date: 2026-08-29
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume-Validated Stop Placement for False Breakouts

## Discovery Summary

N013 establishes that light-volume upside breakouts followed by heavy-volume declines signal false breakouts, while R052 provides structural confirmation filters like percentage and close requirements. N028 identifies this as a bull trap pattern. Combining these: when a breakout fails R052's volume confirmation (light volume per N013), a trader can place a stop just below the breakout level, anticipating the heavy-volume decline described in both N013 and N028 as the confirming signal to exit.

## Trading Implication

A trader should enter short or exit long when an upside breakout occurs on light volume, placing an initial stop above the breakout peak, then aggressively lower the stop below the breakout level once a subsequent heavy-volume decline confirms the bull trap per N013 and N028.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
