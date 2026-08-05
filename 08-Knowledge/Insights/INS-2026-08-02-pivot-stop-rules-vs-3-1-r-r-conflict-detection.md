---
type: insight
date: 2026-08-02
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
# Pivot Stop Rules vs. 3:1 R/R: Conflict Detection

## Discovery Summary

EN071's pivot point buy signal rules specify exact stop placement mechanics (e.g., protective sell stop below current day's low after buy stop election), while RG035 requires stops to satisfy both technical validity AND money management constraints. The conflict emerges when the pivot-defined stop distance (current day's low to entry) produces a risk amount that violates the 5% max risk rule on the account — or when the implied reward target cannot achieve 3:1 given the technically-required stop width. C245 warns that fast-market fills may push the actual stop execution beyond the specified price, further degrading the realized reward/risk ratio.

## Trading Implication

Before entering any pivot point buy signal per EN071, calculate the distance from entry (previous day's high) to the protective stop (current day's low) and verify it satisfies RG035's 5% max risk rule AND allows a reward target at least 3x the stop distance; if not, skip the trade regardless of signal validity.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
