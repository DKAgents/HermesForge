---
type: insight
date: 2026-11-22
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
# Volume Confirms Breakaway Gaps, Flags Exhaustion Gaps

## Discovery Summary

N150 Price Gaps Types distinguishes breakaway, runaway, and exhaustion gaps, while C328 Gaps broadly treats up gaps as strength. R082 Breakouts Must Be Accompanied by Heavy Volume supplies the missing condition: a gap that resembles a pattern breakout is only trustworthy if accompanied by heavy volume. Without that volume confirmation, an up gap can be an exhaustion gap rather than a breakaway, so the volume rule filters which gap type is actually in play.

## Trading Implication

When a gap appears at a potential breakout, check volume before acting: chase volume-confirmed breakaway or runaway gaps, but do not chase unconfirmed gaps and treat light-volume gaps as possible exhaustion/reversal warnings.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
