---
type: insight
date: 2026-09-07
actionability: 3
connection_type: contradicts_assumption
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
---

# Pivot Point Stop Placement Ignores Support Levels

## Discovery Summary

EN071's pivot point buy signal rules set a protective sell stop below the current day's low or below today's open, which are mechanically derived levels. RG035 insists that protective stops must always be placed at valid technical levels — below support for longs — to satisfy both technical and money management criteria. The pivot point rule's automatic stop may land above a key support, forcing either an invalid stop or a violation of the technical requirement, creating a direct conflict between the mechanical entry system and sound stop placement.

## Trading Implication

When executing EN071 pivot point longs, always verify that the prescribed stop (current day's low or open) lies beneath a genuine support level; if not, move the stop below that support and resize the position in line with the widened risk per RG035's position sizing guidance.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**contradicts_assumption** — Actionability score: 3/5
