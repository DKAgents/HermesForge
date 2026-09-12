---
type: insight
date: 2026-09-12
actionability: 4
connection_type: creates_filter
domains: [C245-stop-order, EN071-pivot-point-buy-signal-rules, RG035-combining-technical-factors-with-money-management]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
---

# Pivot Point Stops Can Violate 3:1 Reward/Risk Requirement

## Discovery Summary

EN071's pivot point buy signal rule mandates a protective stop below the current day's low (or today's open), creating a fixed technical risk distance that may be too wide to achieve a 3:1 reward/risk target. RG035 insists stops align with technical levels, but also warns that looser stops reduce position size; here, the technical stop placement conflicts with a required return ratio if no suitable profit target exists at three times the stop distance. A trader must filter these signals by checking whether a logical profit target (e.g., next resistance) extends far enough to meet the 3:1 threshold before entry.

## Trading Implication

Before taking a pivot point buy signal per EN071, calculate the stop distance to the protective level and confirm there is a chart-based target at least three times that distance; if not, either skip the trade or scale the position down per RG035's 5% risk rule until the risk-reward profile becomes acceptable.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**creates_filter** — Actionability score: 4/5
