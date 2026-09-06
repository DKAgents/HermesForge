---
type: insight
date: 2026-09-06
actionability: 3
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
---

# Pivot Point Stops Require Position Sizing

## Discovery Summary

The pivot point buy signal rules (EN071) specify protective stops at technical levels such as below the current day's low or today's open. RG035 stresses that stops must be placed at valid technical levels but also that position size must be adjusted based on stop distance to manage risk. This means the EN071 entry rules provide the technical stop, while RG035's money management overlay requires the trader to calculate the dollar risk from that stop distance and size the position accordingly.

## Trading Implication

When taking a pivot point buy signal, immediately measure the distance from entry to the specified stop level, then adjust position size so that the trade's dollar risk stays within your account's maximum risk limit.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 3/5
