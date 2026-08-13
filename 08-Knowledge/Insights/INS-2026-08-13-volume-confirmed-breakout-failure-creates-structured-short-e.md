---
type: insight
date: 2026-08-13
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume-Confirmed Breakout Failure Creates Structured Short Entry

## Discovery Summary

N013 and N028 jointly establish that a light-volume upside breakout followed by a heavy-volume decline is a 'negative chart combination' signaling a bull trap. R052 provides the mechanical confirmation layer: requiring a close beyond the prior peak (not just intraday) means the false breakout can be identified precisely when price closes back below that peak after failing the volume test. Combined, these three notes produce a sequential decision rule: (1) flag a breakout on light volume as suspect per N013/N028, (2) confirm the trap when price closes back below the breakout level per R052's close-filter, and (3) the heavy-volume decline that follows N028 provides both entry signal and natural stop placement above the failed breakout high.

## Trading Implication

When a breakout occurs on light volume, place a conditional short order triggered by a close back below the breakout resistance level, with a stop just above the false breakout high; the subsequent heavy-volume decline per N028 confirms the trade.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
