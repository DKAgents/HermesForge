---
type: insight
date: 2026-10-12
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
# Pivot entries need trailing stops; exits drive results

## Discovery Summary

EN071-pivot-point-buy-signal-rules addresses the entry side, but Murphy's insight says trade performance is determined more by exits than entries. RG023-pf-trailing-stop-adjustment operationalizes that insight by specifying how to manage the exit, while C245-stop-order provides the order type needed to make the exit explicit and mechanical. The non-obvious link is that a pivot buy signal should be paired with an immediate stop-order and trailing-stop adjustment discipline, not treated as a standalone entry trigger.

## Trading Implication

When a pivot-point buy signal fires, do not focus only on entry timing; immediately place a stop-order and apply the trailing-stop adjustment rule so the exit is predefined and adaptive.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 3/5

## Related Notes
- [[INS-2026-09-30-pivot-entries-need-trailing-stop-exits|Pivot entries need trailing stop exits]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
