---
type: insight
date: 2026-10-02
actionability: 3
connection_type: resolves_conflict
domains: [indicators, patterns, rules]
sources: ["N150-price-gaps-types", "N007-runaway-gap-as-measuring-tool", "EX006-breakaway-gap-bearish-signal"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Gap type determines chase vs fade strategy

## Discovery Summary

Notes N150 defines various gap types (breakaway, runaway, etc.), N007 describes runaway gaps as measuring tools for continuation (chase opportunity), and EX006 explicitly labels breakaway gaps as bearish signals (fade opportunity). This resolves the conflict of whether to chase or fade a gap by requiring classification of the gap type first.

## Trading Implication

When a gap occurs, classify it as a breakaway gap to fade (short) or a runaway gap to chase (go with the trend), using the criteria from N150 and the signals from N007 and EX006.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[N007-runaway-gap-as-measuring-tool]]
- [[EX006-breakaway-gap-bearish-signal]]

## Connection Type

**resolves_conflict** — Actionability score: 3/5
