---
type: insight
date: 2026-10-27
actionability: 4
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
# Exits matter more: stop placement rules edge

## Discovery Summary

Murphy's insight that exits matter more than entries directly supports the logic behind RG023-pf-trailing-stop-adjustment (trailing stops adjust dynamically to lock profits) and C245-stop-order (a stop order defines the exit). EN071-pivot-point-buy-signal-rules likely triggers entries, but the real edge comes from setting the stop correctly, not the entry signal itself. The connection is non-obvious because traders often focus on entry signals, but these notes together imply that the stop placement rule is the primary determinant of risk-adjusted performance.

## Trading Implication

Prioritize trailing stop adjustment rules (RG023) and stop order types (C245) over fine-tuning entry signals; use pivot-based buy signals only if you have a robust exit strategy in place.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[INS-2026-09-16-volume-confirmed-breakout-stop-placement-rule|Volume-Confirmed Breakout Stop Placement Rule]]
- [[INS-2026-10-25-prioritize-trailing-stop-over-pivot-entry|Prioritize trailing stop over pivot entry]]
- [[RG023-pf-trailing-stop-adjustment|P&F Trailing Stop Adjustment]]
- [[C245-stop-order|Stop Order]]
