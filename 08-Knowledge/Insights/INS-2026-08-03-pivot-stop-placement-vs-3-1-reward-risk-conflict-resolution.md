---
type: insight
date: 2026-08-03
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
# Pivot Stop Placement vs 3:1 Reward/Risk: Conflict Resolution

## Discovery Summary

EN071 places the protective sell stop below the current day's low (or today's open in the late-session variant), while RG035 requires stops to be at valid technical levels AND satisfy a 5% maximum risk on total account. The conflict arises when the distance from the pivot buy stop trigger (above prior day's high) to the intraday low stop is too wide to achieve 3:1 reward/risk while staying within the 5% account risk cap. C245 reinforces that fill price may be beyond the stop in fast markets, further widening realized risk. The resolution from RG035 is explicit: if the technically mandated stop violates money management limits, reduce position size rather than move the stop to an invalid level.

## Trading Implication

Before entering any EN071 pivot buy signal, calculate the distance from the buy stop trigger to the protective sell stop and verify it permits both a 3:1 reward/risk ratio and keeps total position risk under 5% of account; if it does not, reduce position size or skip the trade entirely rather than tightening the stop to a technically invalid level.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
