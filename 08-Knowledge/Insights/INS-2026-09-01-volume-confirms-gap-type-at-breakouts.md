---
type: insight
date: 2026-09-01
actionability: 4
connection_type: creates_filter
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Volume Confirms Gap Type at Breakouts

## Discovery Summary

Rule R082 demands heavy volume at all breakouts for validity, while Notes C328 and N150 catalog gap types where breakaway gaps specifically signal new trend initiation. Applying the volume rule to gap identification means a gap can only be treated as a valid breakaway gap (and thus a tradable signal) if it occurs on heavy volume relative to recent activity. Without heavy volume, a gap that looks like a breakaway may instead be a common gap or a false signal, preventing premature entry.

## Trading Implication

Only trade a gap as a breakaway/trend initiation signal if the gap day's volume is significantly above the prior 10-20 day average; if volume is absent, treat the gap as a common gap and wait for a heavy-volume price pattern breakout to confirm direction.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
