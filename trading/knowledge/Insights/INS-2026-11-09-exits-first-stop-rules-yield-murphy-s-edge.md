---
type: insight
date: 2026-11-09
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: Murphy - Technical Analysis of the Financial Markets
---
# Exits First: Stop Rules Yield Murphy's Edge

## Discovery Summary

Murphy's principle that exits matter more than entries is directly operationalized by RG023's P&F trailing stop (raising stops to just below the latest o column) and EN071's pivot point protective stops (placing sell stops below current day's low or open). These provide concrete, mechanical exit adjustments that prioritize capital protection over entry timing, aligning with the stop-order emphasis in C245. The connection is that effective exit management, not entry precision, drives long-term profitability.

## Trading Implication

A trader should predefine and mechanically trail stop orders based on price structure (e.g., P&F columns or pivot day ranges) before or at entry, treating the exit as the primary decision variable.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
- [[C245-stop-order|Stop Order]]
