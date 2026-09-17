---
type: insight
date: 2026-09-17
actionability: 4
connection_type: resolves_conflict
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
---

# Pivot Point Stop and 3:1 R/R Conflict

## Discovery Summary

The pivot point buy signal rules (EN071) specify protective stop placement below the current day's low or today's open. Risk guideline RG035 insists stops must be at valid technical levels but also subject to money management (max 5% risk). A 3:1 reward/risk rule conflicts when the distance from entry to that technical stop is too large relative to a plausible profit target (e.g., next resistance or pivot), making the required reward unattainable or the risk too high for the account. The trader must then decide to skip the trade or reduce position size to satisfy both technical stop location and risk/reward constraints.

## Trading Implication

Before acting on a pivot point buy signal, compute the stop distance from entry to the protective stop level (below today's low or open). Ensure a potential profit target (e.g., prior high or pivot resistance) is at least three times that distance; otherwise, reject the signal or reduce position size to limit dollar risk.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
