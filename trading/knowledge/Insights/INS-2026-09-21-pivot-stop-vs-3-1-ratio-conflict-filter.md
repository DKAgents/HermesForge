---
type: insight
date: 2026-09-21
actionability: 3
connection_type: creates_filter
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Pivot stop vs 3:1 ratio conflict filter

## Discovery Summary

The pivot point buy signal rules (EN071) set a protective stop at a technical level (below current day's low or under today's open). Combined with a 3:1 reward/risk requirement (common but not in notes), this creates a conflict when the stop distance makes a 3x target unattainable or trivial. The money management guideline (RG035) further reinforces that stops must be at valid technical levels and satisfy risk limits, adding a constraint.

## Trading Implication

Before acting on a pivot point buy signal, calculate the stop distance and verify that a realistic target at least 3 times that distance exists (e.g., based on previous resistance or recent high). If not, skip the trade or reduce position size.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**creates_filter** — Actionability score: 3/5

## Related Notes
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
