---
type: insight
date: 2026-08-23
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
# Pivot Stop Placement vs 3:1 Reward/Risk Conflict Detection

## Discovery Summary

EN071 defines mechanically precise stop placement (below current day's low or today's open) while RG035 requires stops to satisfy both technical AND money management criteria simultaneously. The conflict arises when the pivot point stop distance — determined by intraday price structure — produces a reward/risk ratio below 3:1: a stop under today's low may be technically valid per EN071 but violate position-sizing math per RG035. C245 reinforces that fill price may slip beyond the stop in fast markets, further degrading the realized reward/risk ratio from the intended level.

## Trading Implication

Before placing the EN071 pivot buy stop, calculate the distance to the mandatory protective sell stop and verify the measured move target yields at least 3:1 reward/risk; if it does not, skip the trade regardless of the valid technical setup.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5

## Related Notes
- [[INS-2026-08-27-pivot-point-stop-distance-vs-risk-limits-resolution|Pivot Point Stop Distance vs. Risk Limits Resolution]]
