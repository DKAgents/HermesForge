---
type: insight
date: 2026-11-13
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume Confirms Gap Type for Chasing or Fading

## Discovery Summary

The gap types (breakaway, runaway, exhaustion) each signal different trend phases, while R082 states that pattern breakouts require heavy volume to be valid. Thus, a breakaway gap with heavy volume confirms a valid new trend (chase), whereas an exhaustion gap with heavy volume indicates a climax and likely reversal (fade). Volume acts as a confirmation filter for the gap's significance.

## Trading Implication

Classify each gap by its position in the trend; if it's a breakaway gap and volume surges, trade in gap direction; if it's an exhaustion gap and volume spikes, consider fading or exiting.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
