---
type: insight
date: 2026-08-16
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
# Pivot Stop Placement vs 3:1 Reward/Risk Conflict Resolution

## Discovery Summary

EN071 specifies a mechanical stop placement rule (below current day's low or today's open) that may produce stops too tight or too loose relative to technical levels. RG035 requires stops to satisfy both money management criteria (max 5% risk on total account) AND valid technical placement (below support). C245 warns that fast markets can cause fills beyond stop prices. The conflict arises when EN071's intraday stop location is technically arbitrary rather than at a support level, potentially violating RG035's dual-criteria requirement and failing the implicit 3:1 reward/risk test if the entry-to-stop distance is too wide.

## Trading Implication

Before placing the pivot point buy stop per EN071, calculate the distance from entry (previous day's high) to the mechanical stop (current day's low or today's open), verify it satisfies the 5% max risk rule from RG035, and confirm it aligns with a valid technical support level — skip the trade if any criterion fails.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
