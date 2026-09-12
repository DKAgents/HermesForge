---
type: insight
date: 2026-09-11
actionability: 4
connection_type: adds_condition
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Pivot point entry rules can violate reward/risk requirements

## Discovery Summary

EN071's pivot-point buy signal rule specifies a protective stop below the current day's low, determining risk after entry. When that technical stop distance implies a risk amount, taking a full position under RG035's 5% risk rule may produce a reward target that fails a 3:1 ratio if the technical objective is too close. The conflict arises because EN071 mandates a technically-placed stop while a 3:1 requirement imposes a minimum profit target; if the distance from entry to the next resistance is less than three times the stop distance, the trade must be skipped or size must be reduced below RG035's maximum to maintain the ratio without moving the stop from its technical level.

## Trading Implication

Before placing the EN071 buy stop, calculate whether the distance to the next identifiable resistance level is at least three times the stop distance below today's low; skip the trade if it fails this test, even if all other pivot-point conditions are met.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 4/5
