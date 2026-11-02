---
type: insight
date: 2026-11-01
actionability: 4
connection_type: creates_filter
domains: [concepts, patterns, trading_rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume Filters Breakaway vs Exhaustion Gaps for Trading

## Discovery Summary

N150-price-gaps-types and C328-gaps define breakaway gaps as trend starts and exhaustion gaps as trend ends, but R082-breakouts-must-be-accompanied-by-heavy-volume adds the missing validation: a breakaway gap is only a real breakout if it occurs with heavy volume. A gap without volume expansion at a pattern boundary is more likely a common gap or false breakout, while a gap after an extended trend—especially after a runaway/measuring gap target is reached—should be treated as an exhaustion gap and considered for fading. This turns gap taxonomy into a volume-filtered chase-vs-fade decision rule.

## Trading Implication

Chase a gap only if it appears at a breakout point with heavy volume; otherwise treat it as a common gap and stand aside. Fade gaps that occur after an extended move or after a measured target is reached, as they likely signal exhaustion.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
