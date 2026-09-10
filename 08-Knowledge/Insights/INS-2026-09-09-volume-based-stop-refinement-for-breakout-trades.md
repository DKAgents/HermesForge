---
type: insight
date: 2026-09-09
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume-Based Stop Refinement for Breakout Trades

## Discovery Summary

N013 states that valid breakouts need heavy volume, while false breakouts occur on light volume with subsequent heavy-volume declines. R052 adds confirmation filters like the two-day close rule. N028 describes the bull trap pattern. Combining these: after entering on a breakout confirmed by R052's close filter, monitor post-entry volume—if the breakout was on light volume and a decline begins on increasing volume, treat the pattern as a probable bull trap (N028) and place stops tighter below the breakout level rather than giving it the full filter tolerance.

## Trading Implication

When a breakout meets R052's two-day close filter but occurred on light volume, tighten the protective stop to just below the breakout level and exit immediately if a heavy-volume decline follows, treating it as a likely N028 bull trap.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**adds_condition** — Actionability score: 4/5
