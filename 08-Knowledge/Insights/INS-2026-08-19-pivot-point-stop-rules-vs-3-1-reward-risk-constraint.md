---
type: insight
date: 2026-08-19
actionability: 4
connection_type: resolves_conflict
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
---

# Pivot Point Stop Rules vs 3:1 Reward/Risk Constraint

## Discovery Summary

EN071 specifies that a protective sell stop is placed below the current day's low after a buy stop is elected — a mechanically fixed stop distance. RG035 requires that stops be placed at valid technical levels while also satisfying a 5% maximum dollar risk rule on the total account. The conflict emerges when the current day's low is far from the entry (wide intraday range), forcing the dollar risk to exceed the 5% cap unless position size is reduced — but the seed question's 3:1 reward/risk requirement adds a third constraint: if the stop is too tight (e.g., placed under today's open per EN071's late-day rule), the required 3:1 target may project beyond a reasonable technical objective. EN071's dual stop rules (under today's low vs. under today's open) thus create asymmetric reward/risk profiles that must be screened against both RG035's dollar limits and a 3:1 target feasibility check before entry.

## Trading Implication

Before executing an EN071 pivot point buy signal, calculate position size using RG035's 5% risk cap against whichever EN071 stop is applicable (day's low or today's open), then verify the resulting 3:1 reward target is achievable given nearby resistance; if not, skip the trade regardless of the signal.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
