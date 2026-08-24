---
type: insight
date: 2026-08-06
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
# Pivot Stop Placement vs. 3:1 Reward/Risk Conflict Resolution

## Discovery Summary

EN071 specifies mechanical stop placement (below current day's low or today's open) driven by intraday pivot logic, while RG035 requires stops to satisfy both technical validity AND money management constraints (max 5% account risk). A conflict arises when the pivot-mandated stop distance is too wide to achieve 3:1 reward/risk on the available target, or forces position sizing so small it becomes impractical. C245 confirms that in fast markets, fills may exceed the stop price, further degrading the reward/risk ratio beyond what the pivot rules anticipate.

## Trading Implication

Before entering a pivot point buy signal per EN071, calculate whether the distance from entry (above previous day's high) to the protective stop (below current day's low) allows a 3:1 reward/risk target; if not, skip the trade rather than override the stop to a technically invalid level, as RG035 prohibits placing stops outside valid technical levels purely for money management convenience.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5

## Related Notes
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
