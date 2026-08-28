---
type: insight
date: 2026-07-30
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
# Pivot Stop Rules vs 3:1 Reward/Risk: Position Sizing Conflict

## Discovery Summary

EN071 defines a specific intraday stop placement rule (below current day's low or today's open), while RG035 requires stops to be placed at valid technical levels AND satisfy money management limits (max 5% risk on total account). The conflict arises when the pivot point buy signal's technically-mandated stop is so far from entry that it violates the 5% maximum risk rule or fails a 3:1 reward/risk threshold — forcing a choice between technical validity and position sizing discipline. C245 warns that fast markets may cause fills beyond the stop price, further eroding the reward/risk ratio calculated at entry. The resolution is that RG035 explicitly states position size must shrink when stops are looser, meaning pivot point trades with wide stops require reduced size rather than stop compromise.

## Trading Implication

Before entering a pivot point buy signal per EN071, calculate whether the technically-required stop (below day's low or today's open) allows a 3:1 reward/risk at the day's likely resistance target; if not, either reduce position size per RG035 or skip the trade entirely — never move the stop closer purely to satisfy reward/risk math.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5

## Related Notes
- [[RG022-pf-stop-placement-rule|P&F Stop Placement Rule]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]

## Related
- [[RG020-protective-sell-stops-on-point-and-figure-charts]] — See RG020 for a stop-tightening technique that may reconcile technical and risk constraints.
