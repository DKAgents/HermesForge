---
type: insight
date: 2026-09-30
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N150-price-gaps-types", "N007-runaway-gap-as-measuring-tool", "EX006-breakaway-gap-bearish-signal"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Chase Runaway Gaps, Fade Breakaway Bearish

## Discovery Summary

N150-price-gaps-types distinguishes gap categories (breakaway, runaway, exhaustion, common). N007-runaway-gap-as-measuring-tool treats the runaway gap as a continuation signal often used to project price targets. EX006-breakaway-gap-bearish-signal flags a breakaway gap as a bearish reversal signal. Combining them: a runaway gap after an established trend warrants chasing the trend, while a breakaway gap at a resistance level should be faded short.

## Trading Implication

When a gap occurs, classify it using N150's criteria: if it is a runaway gap (mid-trend, high volume), buy the continuation; if it is a breakaway gap (out of a range, bearish context per EX006), sell or short the reversal.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[N007-runaway-gap-as-measuring-tool]]
- [[EX006-breakaway-gap-bearish-signal]]

## Connection Type

**creates_filter** — Actionability score: 4/5
