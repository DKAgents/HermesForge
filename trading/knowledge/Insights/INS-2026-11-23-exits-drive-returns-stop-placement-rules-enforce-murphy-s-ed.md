---
type: insight
date: 2026-11-23
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
# Exits Drive Returns: Stop Placement Rules Enforce Murphy's Edge

## Discovery Summary

Murphy's insight that exits matter more than entries is directly operationalized by the stop placement rules in RG023 and EN071. RG023's P&F trailing stop systematically raises protective stops as trends advance, while EN071 specifies exact buy stop entry levels and protective sell stops below the low/open. Both prioritize where to exit over when to enter, confirming that well-defined stop rules are the core of trade management.

## Trading Implication

Traders should allocate more effort to defining and trailing stops (e.g., using P&F columns or pivot point levels) than to perfecting entry timing, since stop discipline determines long-run profitability.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
- [[INS-2026-09-16-volume-confirmed-breakout-stop-placement-rule|Volume-Confirmed Breakout Stop Placement Rule]]
