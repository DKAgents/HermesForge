---
type: insight
date: 2026-09-08
actionability: 4
connection_type: adds_condition
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Apply P&F Trailing Stops to Pivot Point Entries

## Discovery Summary

Murphy's emphasis that exits matter more aligns with his stop order guidance in C245-stop-order. The pivot point entry system (EN071-pivot-point-buy-signal-rules) provides specific entry triggers and initial protective stops, but lacks a profit-protecting trailing mechanism. The P&F trailing stop technique in RG023-pf-trailing-stop-adjustment — raising stops to just below the latest o column in an uptrend — can be overlaid onto the pivot point entries to systematically trail the initial stop, transforming a purely entry-focused rule set into a complete exit-aware strategy.

## Trading Implication

After a pivot point buy signal triggers, replace the static protective stop with a trailing stop raised to just below the latest P&F o column low as the trend progresses, directly implementing Murphy's exit priority.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 4/5
