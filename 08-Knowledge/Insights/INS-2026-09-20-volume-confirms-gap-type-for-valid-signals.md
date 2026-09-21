---
type: insight
date: 2026-09-20
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
# Volume Confirms Gap Type for Valid Signals

## Discovery Summary

C328-gaps and N150-price-gaps-types explain gap types and their implications (e.g., breakaway gaps signal trend start, exhaustion gaps signal trend end). R082-breakouts-must-be-accompanied-by-heavy-volume adds a critical volume condition: for any gap to be considered a valid breakout signal, it must be accompanied by heavy volume. This directly links the gap's reliability to volume confirmation, resolving ambiguity about whether a gap is genuine or a trap.

## Trading Implication

When trading gaps, only act on breakaway or runaway gaps that occur with above-average volume; disregard gaps on low volume as likely to be filled (common gaps) or false signals. For exhaustion gaps, expect volume to be high but price to stall or reverse, confirming trend exhaustion.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
