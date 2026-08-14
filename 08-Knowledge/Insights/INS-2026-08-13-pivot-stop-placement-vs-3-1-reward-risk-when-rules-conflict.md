---
type: insight
date: 2026-08-13
actionability: 4
connection_type: resolves_conflict
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Pivot Stop Placement vs. 3:1 Reward/Risk: When Rules Conflict

## Discovery Summary

EN071 specifies mechanical stop placement rules (below current day's low, or below today's open in the late-day variant) that are purely time/price-driven, while RG035 requires stops to be placed at valid technical levels AND satisfy a 5% maximum risk constraint on total account exposure. The conflict emerges when the EN071-mandated stop distance produces a reward/risk ratio below 3:1 — the pivot entry's mechanical stop may be technically valid but financially oversized relative to the position limit. C245 clarifies that stop orders may fill beyond the stop price in fast markets, further degrading the realized reward/risk ratio from what was calculated at order entry.

## Trading Implication

Before placing the EN071 pivot buy stop, calculate whether the distance from entry (previous day's high) to the EN071 protective stop (current day's low or today's open) satisfies both the RG035 5% account risk cap and a minimum 3:1 reward/risk target; if either condition fails, skip the trade rather than adjusting the stop away from its required technical level.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
