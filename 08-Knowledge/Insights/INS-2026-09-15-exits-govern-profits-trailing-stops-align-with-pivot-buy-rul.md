---
type: insight
date: 2026-09-15
actionability: 4
connection_type: adds_condition
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Exits govern profits: trailing stops align with pivot buy rules

## Discovery Summary

Murphy's emphasis on exits is operationalized by RG023's trailing stop rule, which dictates raising protective stops to just below the latest o column in an uptrend. EN071's pivot point buy signal also embeds exit logic by requiring a protective sell stop below the current day's low after entry, and below today's open for the later entry. This shows that stop placement is not merely a risk cap but a profit-locking mechanism that should be tracked as the trend develops, consistent with C245's description of trailing stops to protect profits.

## Trading Implication

When executing a pivot point buy per EN071, trail the protective sell stop upward with each new column of o's in an uptrend, as per RG023, rather than keeping it static at the entry-day low. This converts the exit into an active profit management tool, embodying Murphy's principle that exits matter more than entries.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 4/5
