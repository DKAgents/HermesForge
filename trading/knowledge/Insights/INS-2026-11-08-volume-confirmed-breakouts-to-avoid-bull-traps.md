---
type: insight
date: 2026-11-08
actionability: 3
connection_type: adds_condition
domains: [indicators, patterns, trading_rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume-Confirmed Breakouts to Avoid Bull Traps

## Discovery Summary

R052-filters-for-confirming-breakouts already lists multiple confirmation techniques including volume examination, while N013-volume-as-a-filter-for-false-breakouts specifies that valid upside breakouts require heavy volume, and a light-volume breakout followed by a heavy-volume decline is negative. N028-bull-trap-false-upside-breakout names this exact sequence as a bull trap. Together they form a practical confirmation sequence: apply R052's price/penetration filters, then add N013's volume condition; if the breakout is on light volume and reverses on heavy volume, classify it as N028's bull trap.

## Trading Implication

Do not enter an upside breakout without heavy volume confirmation; if a light-volume breakout is followed by a heavy-volume decline, treat it as a false breakout and exit or avoid long positions. Use a protective stop below the breakout level to limit risk if the trap triggers.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**adds_condition** — Actionability score: 3/5
