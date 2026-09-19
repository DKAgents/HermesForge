---
type: insight
date: 2026-09-18
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
# Pivot stop vs 3:1 reward/risk conflict

## Discovery Summary

The pivot point buy signal rules (EN071) mandate specific stop placements (below today's low or open). The money management guideline (RG035) reinforces using technical levels for stops. When a 3:1 reward/risk requirement is added, the stop distance implied by these levels may be too large relative to the potential profit target (e.g., previous day's high or a measured move), causing the signal to fail the risk check. This creates a conflict: following the strict pivot stop violates the reward/risk rule, so the trader must pre-calculate the ratio and reject signals where it is below 3:1.

## Trading Implication

Before executing a pivot point buy signal, compute the stop distance from entry to the specified stop level and compare it to the expected target; only take the trade if the potential profit is at least three times the stop distance.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
