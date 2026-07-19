---
type: insight
date: 2026-07-19
actionability: 4
connection_type: resolves_conflict
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
---

# Pivot Stop Placement May Violate 3:1 Reward/Risk Threshold

## Discovery Summary

EN071 specifies precise mechanical stop placement rules for pivot point trades (below current day's low, or below today's open for late-session entries), but these technically-derived stops may not satisfy the 3:1 reward/risk requirement implied by RG035's money management framework. RG035 states stops must satisfy BOTH technical AND money management criteria — meaning a technically valid stop under today's low could still be disqualifying if the distance to that stop versus the profit target fails to achieve a minimum reward/risk ratio. C245 further complicates this by noting fill prices in fast markets (e.g., breakout opens above prior high) may be beyond the stop price, widening actual risk beyond the planned stop distance and further compressing the reward/risk ratio.

## Trading Implication

Before entering a pivot point breakout per EN071, a trader should calculate the distance from entry to the prescribed protective stop and verify it supports at least a 3:1 reward/risk ratio against the identified target; if it does not, the trade should be skipped or position size reduced per RG035's maximum 5% risk rule rather than overriding the stop placement.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
