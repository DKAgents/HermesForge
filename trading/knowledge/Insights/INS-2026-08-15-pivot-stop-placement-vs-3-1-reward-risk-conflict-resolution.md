---
type: insight
date: 2026-08-15
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

EN071 defines pivot point buy signal rules where the protective sell stop is placed below the current day's low — a technically derived level. RG035 requires stops to satisfy both technical AND money management criteria, with a maximum 5% risk on total account. The conflict emerges when the technically valid stop (below today's low per EN071) is too far from entry to achieve a 3:1 reward/risk ratio within the 5% account risk constraint. RG035 explicitly states that looser stops require smaller position sizes, meaning the pivot trade may only be viable with a reduced position that still respects the technical stop level — never moving the stop to satisfy reward/risk math.

## Trading Implication

When the pivot point buy stop is elected and the required protective stop (below current day's low) violates the 3:1 reward/risk threshold, do not tighten the stop to a non-technical level — instead reduce position size to bring dollar risk within the 5% limit, or skip the trade entirely if the technical stop is too wide to make the trade worthwhile.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5

## Related Notes
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
