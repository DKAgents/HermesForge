---
type: insight
date: 2026-09-20
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, trading_rules, volume_analysis]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume-Confirmed Breakouts Avoid Bull-Trap Stops

## Discovery Summary

R052-filters-for-confirming-breakouts lists close/percentage/two-day/Friday filters and volume as a reliability clue. N013 and N028 add the specific false-breakout condition: a light-volume upside breakout followed by a heavy-volume decline is a negative combination, meaning the breakout is a bull trap. Together they turn volume from a static confirmation filter into a dynamic exit/stop trigger: any long entered on a confirmed breakout should be exited when a post-breakout decline occurs on heavy volume after the breakout itself was on light volume.

## Trading Implication

Require heavy volume to confirm any upside breakout before entering; if a light-volume breakout is followed by a heavy-volume decline, treat it as a failed breakout/bull trap and exit longs immediately rather than holding for a larger loss.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**adds_condition** — Actionability score: 4/5
