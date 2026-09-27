---
type: insight
date: 2026-09-15
actionability: 3
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
# Pivot stop vs 3:1 reward/risk conflict

## Discovery Summary

The pivot point buy signal rules (EN071) specify placing a protective sell stop below the current day's low or open, but RG035 requires stops to satisfy both technical and money management criteria. If the technical stop distance is too narrow, achieving a 3:1 reward/risk ratio may be impossible without an unrealistic target, forcing traders to adjust position size or skip the trade. This resolves the conflict by requiring traders to validate that the potential reward (based on a reasonable target) is at least three times the stop distance before entering.

## Trading Implication

Before acting on a pivot point buy signal, compute the stop distance from the entry to the technical stop (below today's low or open) and ensure a target at least three times that distance exists; if not, reduce position size or skip the trade.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 3/5

## Related Notes
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
