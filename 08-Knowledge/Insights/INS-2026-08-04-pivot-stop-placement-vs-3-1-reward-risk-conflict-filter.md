---
type: insight
date: 2026-08-04
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
# Pivot Stop Placement vs. 3:1 Reward/Risk Conflict Filter

## Discovery Summary

EN071 specifies mechanical stop placement rules (below current day's low or today's open) that are time- and price-driven, while RG035 requires stops to satisfy both technical levels AND money management constraints (max 5% risk on total account). The conflict emerges when the pivot-point-defined stop distance is too large relative to the entry price to achieve a 3:1 reward/risk ratio — the mechanically-correct technical stop may force a position size so small it violates the 10% commitment rule, or conversely, the technically-valid stop may be so loose that the required target becomes unrealistic. C245 further warns that fast markets can cause fills beyond the stop price, widening actual risk beyond the planned technical level, further degrading the reward/risk ratio.

## Trading Implication

Before entering a pivot-point buy signal per EN071, calculate whether the distance from entry to the mechanical stop (below current day's low or today's open) allows a 3:1 reward target at a realistic price level; if not, skip the trade rather than adjusting the stop to a technically invalid level.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5

## Related Notes
- [[RG022-pf-stop-placement-rule|P&F Stop Placement Rule]]
