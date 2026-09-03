---
type: insight
date: 2026-07-26
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
# Pivot Stop Distance May Invalidate 3:1 Reward/Risk Ratio

## Discovery Summary

EN071-pivot-point-buy-signal-rules mandates that the protective sell stop be placed below the current day's low — a technically-driven distance the trader cannot choose. RG035-combining-technical-factors-with-money-management-for-stop-p establishes that stops must sit at valid technical levels AND satisfy money management constraints (max 5% portfolio risk). The conflict emerges when the current day's low is far from the buy stop trigger above the previous day's high: the technically required stop distance may produce a reward/risk ratio below 3:1 if the measured target is not at least 3x that distance away. C245-stop-order further warns that in fast markets, actual fill on the buy stop may be beyond the trigger price, widening the realized risk and compressing the reward/risk ratio further, potentially below the 3:1 threshold even when pre-trade math appeared acceptable.

## Trading Implication

Before entering a pivot-point buy signal per EN071, calculate the distance from the buy stop trigger to the current day's low stop; only take the trade if a realistic price target exists at 3x that distance AND the resulting position size satisfies the 5% maximum risk rule from RG035 — if either condition fails, skip the signal that day.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5

## Related
- [[RG023-pf-trailing-stop-adjustment]] — Trailing stop method that can later reduce the pivot stop's reward/risk constraint

- [[RG003-protective-stop-placement-relative-to-round-numbers]] — See RG003-protective-stop-placement-relative-to-round-numbers for round-number constraint on pivot stops
