---
type: insight
date: 2026-09-11
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Volume-Confirm Breakaway Gaps to Avoid False Signals

## Discovery Summary

R082 mandates that all breakout signals must be accompanied by heavy volume to be considered valid. N150 defines breakaway gaps as signals that start a new trend, effectively functioning as breakout events. Applying R082's volume rule to breakaway gaps creates a filter: a gap upward on heavy volume confirms a genuine breakaway, whereas a gap on ordinary volume may indicate a common gap that is likely to fail.

## Trading Implication

Only trade a breakaway gap if it occurs with a clear volume surge; if volume is missing, treat the move as a common gap to be faded or ignored.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
