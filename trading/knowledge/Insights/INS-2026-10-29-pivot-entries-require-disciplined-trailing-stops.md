---
type: insight
date: 2026-10-29
actionability: 3
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Pivot Entries Require Disciplined Trailing Stops

## Discovery Summary

EN071-pivot-point-buy-signal-rules defines a specific entry trigger, but Murphy's insight that exits matter more than entries elevates the importance of RG023-pf-trailing-stop-adjustment. The C245-stop-order concept supplies the execution mechanism for exiting and trailing positions. Therefore, pivot point buy signals should not be used without a corresponding stop placement and trailing stop plan to lock in profits and limit losses.

## Trading Implication

When a pivot point buy signal fires, immediately pair it with a stop order and follow RG023's trailing stop adjustment rules to manage the exit. Prioritize setting and updating stops over fine-tuning the entry signal.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 3/5

## Related Notes
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
