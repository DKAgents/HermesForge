---
type: insight
date: 2026-10-03
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N150-price-gaps-types", "N007-runaway-gap-as-measuring-tool", "EX006-breakaway-gap-bearish-signal"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Gap type dictates chase vs fade strategy

## Discovery Summary

N150 categorizes gap types, EX006 specifies breakaway gaps as a bearish signal (fade), while N007 treats runaway gaps as a measuring tool for continuation (chase). Combining these notes gives a clear rule: breakaway gaps warrant fading (short), runaway gaps warrant chasing (long) with a measured move target.

## Trading Implication

If a breakaway gap forms, fade by taking a short position; if a runaway gap forms, chase by going long and project the gap's measuring distance as a target.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[N007-runaway-gap-as-measuring-tool]]
- [[EX006-breakaway-gap-bearish-signal]]

## Connection Type

**adds_condition** — Actionability score: 4/5
