---
type: insight
date: 2026-09-07
actionability: 4
connection_type: creates_filter
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
---

# Heavy Volume Confirms Breakaway Gaps and Island Reversals

## Discovery Summary

N150 classifies breakaway gaps as trend-start signals and describes island reversals as an exhaustion gap followed by an opposite breakaway gap. R082 requires breakout signals to be accompanied by heavy volume for validity. Applying that rule to gap structure creates a filter: the breakaway gap itself, or the breakaway leg of an island reversal, should show a volume surge; without it the gap-based signal is suspect.

## Trading Implication

Treat a breakaway gap as tradeable only if it prints on heavy volume; for an island reversal, wait for the opposite breakaway gap to occur with heavy volume before fading the prior trend.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
