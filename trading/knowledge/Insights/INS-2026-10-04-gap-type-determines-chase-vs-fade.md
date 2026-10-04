---
type: insight
date: 2026-10-04
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N150-price-gaps-types", "N007-runaway-gap-as-measuring-tool", "EX006-breakaway-gap-bearish-signal"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Gap Type Determines Chase vs Fade

## Discovery Summary

N150 categorizes gap types, EX006 specifies that a breakaway gap (bearish) is a signal to sell (fade), while N007 indicates a runaway gap serves as a measuring tool for trend continuation (chase). This distinction allows a trader to decide action based on gap type: fade breakaway gaps, chase runaway gaps.

## Trading Implication

Upon identifying a gap, classify it using N150: if it's a breakaway gap (especially bearish), initiate a fade trade; if it's a runaway gap, ride the trend using the measuring tool from N007.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[N007-runaway-gap-as-measuring-tool]]
- [[EX006-breakaway-gap-bearish-signal]]

## Connection Type

**adds_condition** — Actionability score: 4/5
