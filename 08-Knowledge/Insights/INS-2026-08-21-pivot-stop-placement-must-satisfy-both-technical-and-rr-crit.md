---
type: insight
date: 2026-08-21
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
# Pivot Stop Placement Must Satisfy Both Technical and RR Criteria

## Discovery Summary

EN071 specifies exact mechanical stop placement rules (below current day's low or today's open) for pivot point buy signals, but RG035 requires that stops must simultaneously satisfy money management criteria — specifically a maximum 5% account risk. The conflict arises when the technically-dictated stop distance from EN071 implies a position size that violates the 10% maximum commitment rule from RG035, or when the stop is so tight that a 3:1 reward/risk ratio cannot be achieved given the day's range. C245 reinforces that stop orders in fast markets may fill beyond the stop price, further degrading the realized reward/risk ratio from what was calculated at order placement.

## Trading Implication

Before placing the pivot point buy stop per EN071, calculate position size using RG035's 5% max risk constraint; if the technically-valid stop distance forces a position too small to be meaningful, or if the implied reward target cannot reach 3:1 given current price structure, skip the trade entirely.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5

## Related Notes
- [[RG022-pf-stop-placement-rule|P&F Stop Placement Rule]]
- [[C245-stop-order|Stop Order]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
