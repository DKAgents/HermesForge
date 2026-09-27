---
type: insight
date: 2026-08-06
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Multi-Filter False Breakout System with Volume-Based Stop Placement

## Discovery Summary

N013 and N028 establish that light-volume breakouts followed by heavy-volume reversals are the diagnostic signature of a bull trap, while R052 provides five concrete confirmation filters (close-based, percentage, two-day, Friday-close, volume) to screen breakouts before entry. The non-obvious connection is that combining R052's pre-entry filters with N013/N028's post-breakout volume behavior creates a two-stage decision system: first gate entry through R052's filters, then monitor volume dynamics to determine stop placement — a light-volume breakout that survives R052 filters but then shows heavy-volume decline (N028's 'negative chart combination') becomes a stop-trigger signal rather than a hold signal.

## Trading Implication

A trader should require at least two R052 filters to confirm a breakout before entering, then set a stop below the breakout level conditioned on heavy-volume reversal — if a confirmed breakout subsequently shows heavy distribution volume on decline, exit immediately rather than waiting for price-based stop execution.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
