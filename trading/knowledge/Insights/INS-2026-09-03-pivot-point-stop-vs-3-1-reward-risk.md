---
type: insight
date: 2026-09-03
actionability: 3
connection_type: creates_filter
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Pivot Point Stop vs. 3:1 Reward/Risk

## Discovery Summary

The Pivot Point Buy Signal Rules (EN071) place a protective stop below the current day’s low, a technical level that may be wide. RG035 mandates stops at valid technical levels and limits risk to a fixed percentage of account equity (e.g., 5%), adjusting position size accordingly. When a trader adds a 3:1 reward/risk requirement, the distance from entry to this technical stop can easily exceed what the expected profit target can support, creating a direct conflict between the signal’s stop logic and the ratio rule. This mismatch acts as a filter to avoid trades where the forced technical stop yields an unacceptable risk-reward profile.

## Trading Implication

Before executing a pivot point buy signal, measure the risk distance to the required protective stop; only take the trade if the anticipated reward (from pivot targets or range projections) is at least three times that distance.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**creates_filter** — Actionability score: 3/5

## Related Notes
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
