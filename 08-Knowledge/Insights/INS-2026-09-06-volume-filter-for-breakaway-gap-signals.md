---
type: insight
date: 2026-09-06
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Volume Filter for Breakaway Gap Signals

## Discovery Summary

N150 and C328 define breakaway gaps as signaling the start of a new trend, while R082 requires all price pattern breakouts to show heavy volume for validity. Connecting these, a breakaway gap—often a breakout from consolidation—should be confirmed by a volume surge; otherwise, the gap signal is unreliable. This turns a gap type from a standalone signal into a filtered entry requiring volume confirmation.

## Trading Implication

Only chase a breakaway gap if it occurs on significantly higher volume than recent bars; fade or ignore breakaway gaps that lack volume surge, as they likely represent false breakouts.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
