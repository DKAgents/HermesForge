---
type: insight
date: 2026-08-20
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
# Pivot Stop Rules vs 3:1 Reward/Risk: Sizing Conflicts

## Discovery Summary

EN071's pivot point buy signal places a protective stop below the current day's low, but this technically-derived stop distance may not satisfy the 3:1 reward/risk requirement implied by RG035's money management framework. RG035 explicitly states stops must satisfy BOTH technical and money management criteria — meaning if the distance from entry (above prior day's high) to the pivot stop (below current day's low) is too wide, the position size must be reduced, not the stop moved. C245 further warns that fast market fills can push actual stop execution beyond the intended price, widening the effective risk even further beyond the planned level.

## Trading Implication

Before entering a pivot point buy signal per EN071, calculate whether the entry-to-stop distance (prior day's high to current day's low) allows a 3:1 reward/risk ratio given your target; if not, either reduce position size per RG035 or skip the trade rather than tightening the stop to an invalid technical level.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
