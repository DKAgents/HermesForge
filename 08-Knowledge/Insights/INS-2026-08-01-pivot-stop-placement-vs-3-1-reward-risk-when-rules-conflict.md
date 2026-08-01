---
type: insight
date: 2026-08-01
actionability: 4
connection_type: resolves_conflict
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
---

# Pivot Stop Placement vs. 3:1 Reward/Risk: When Rules Conflict

## Discovery Summary

EN071's pivot point rules place a protective sell stop below the current day's low after entry above the previous day's high — a technically valid location per RG035's requirement to place stops below support. However, RG035's money management framework (max 5% risk on total account) creates a position-sizing constraint that may conflict with EN071's fixed stop location: if today's low is far from entry, the stop distance may force position size below a meaningful threshold or violate the 10% max commitment rule. C245 further notes that in fast markets, the actual fill may exceed the stop price, widening realized risk beyond what RG035's 5% cap allows.

## Trading Implication

Before entering any EN071 pivot buy signal, calculate the distance from the entry (above prior day's high) to the protective stop (below current day's low) and verify that position size satisfying RG035's 5% max risk rule still produces a 3:1 reward/risk ratio; if not, skip the trade regardless of the technical signal.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
