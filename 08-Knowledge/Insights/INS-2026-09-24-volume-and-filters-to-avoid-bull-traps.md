---
type: insight
date: 2026-09-24
actionability: 3
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume and filters to avoid bull traps

## Discovery Summary

N013 ('Volume as a Filter for False Breakouts') and N028 ('Bull Trap') both highlight that a valid upside breakout should occur on heavy volume, while a false breakout (bull trap) often happens on light volume followed by a decline on heavy volume. R052 ('Filters for Confirming Breakouts') provides additional confirmations like close beyond resistance and percentage penetration. Integrating these suggests that after a breakout, a trader should check volume: if it's light, treat it as a potential bull trap and place a stop just below the breakout level or wait for further confirmation.

## Trading Implication

When a breakout occurs on light volume, either avoid entering or place a stop-loss just below the breakout level to protect against a potential bull trap, and only add to the position after heavy volume confirmation.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**adds_condition** — Actionability score: 3/5
