---
type: insight
date: 2026-09-27
actionability: 4
connection_type: adds_condition
domains: [patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Volume confirms breakaway gaps as valid breakouts

## Discovery Summary

The 'Price Gaps Types' note defines breakaway gaps as signals of new trends, while 'Breakouts Must Be Accompanied by Heavy Volume' states that all pattern breakouts require heavier volume to be valid. Applying this rule to breakaway gaps means that a gap without a volume surge is likely a common gap or false signal, not a genuine breakout.

## Trading Implication

Only enter trades on breakaway gaps if the gap is accompanied by a significant increase in volume; otherwise, treat the gap as a common gap and avoid trading it as a trend signal.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
