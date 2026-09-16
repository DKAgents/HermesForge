---
type: insight
date: 2026-09-16
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, risk management, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume-Confirmed Breakout Stop Placement Rule

## Discovery Summary

The notes N013 and N028 both emphasize that a valid upside breakout requires heavy volume, while a false breakout (bull trap) is often on light volume followed by a heavy-volume decline. This directly supports R052's filters for confirming breakouts, which include price and time filters but notably lack explicit volume-based stop logic. Synthesizing these, a trader can add a volume condition to R052: after a close above resistance with light volume, a subsequent heavy-volume down bar signals a failed breakout, triggering an immediate stop-loss.

## Trading Implication

When entering a breakout, place a sell stop below the breakout bar's low or the recent pullback low, and if the breakout was on light volume, tighten the stop by placing it at the breakout level itself. Additionally, if a heavy-volume down bar occurs within 2-3 days of a light-volume breakout, exit immediately rather than waiting for a price stop.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
