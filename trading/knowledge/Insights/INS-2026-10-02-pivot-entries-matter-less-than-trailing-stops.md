---
type: insight
date: 2026-10-02
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Pivot entries matter less than trailing stops

## Discovery Summary

EN071-pivot-point-buy-signal-rules defines the entry, but Murphy's insight that exits matter more than entries directly supports the emphasis in RG023-pf-trailing-stop-adjustment on managing the exit. C245-stop-order provides the execution mechanism to implement a disciplined trailing stop. The combination reveals that the real edge comes from post-entry stop management, not the pivot signal itself.

## Trading Implication

After a pivot point buy signal triggers per EN071, immediately set and trail a stop according to RG023 using a C245 stop order, prioritizing exit management over further entry refinement.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
