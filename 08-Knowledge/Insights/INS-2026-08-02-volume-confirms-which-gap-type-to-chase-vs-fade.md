---
type: insight
date: 2026-08-02
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume Confirms Which Gap Type to Chase vs Fade

## Discovery Summary

N150 and C328 establish that gap types carry opposite implications: breakaway and runaway gaps signal continuation (chase), while exhaustion gaps signal reversal (fade). R082 adds the critical filter missing from the gap taxonomy: volume validation. A breakaway gap on heavy volume confirms a new trend worth chasing, while a gap on diminishing or absent volume is more likely an exhaustion gap to fade. The island reversal pattern described in N150 (exhaustion gap + opposite breakaway gap) would require two consecutive volume surges to be fully confirmed per R082.

## Trading Implication

When a gap forms, immediately check volume: a gap accompanied by a surge in volume above average should be traded in the direction of the gap (chase); a gap on light or declining volume is a candidate fade, as it likely signals exhaustion rather than breakout strength.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
