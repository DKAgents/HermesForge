---
type: insight
date: 2026-09-02
actionability: 3
connection_type: confirms_risk_rule
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume filter confirms breakout rules and bull trap patterns

## Discovery Summary

The volume filter in N013 directly supports the breakout confirmation filters listed in R052, which include volume as a key reliability clue. N028's bull trap pattern demonstrates the negative outcome when a breakout on light volume is followed by heavy-volume decline, validating the need for multiple confirmation techniques.

## Trading Implication

Require heavy volume on upside breakouts as a condition for entry, in addition to price-based filters like a close beyond the peak or a two-day rule; exit immediately if a breakout occurs on light volume and then reverses on heavy volume.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**confirms_risk_rule** — Actionability score: 3/5
