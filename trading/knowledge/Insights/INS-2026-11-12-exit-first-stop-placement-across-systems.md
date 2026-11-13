---
type: insight
date: 2026-11-12
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
# Exit-First Stop Placement Across Systems

## Discovery Summary

Murphy's principle that exits matter more than entries is operationalized by the specific stop placement techniques in RG023 (P&F trailing stop to latest o/x column), C245 (stop order mechanics and trailing upward), and EN071 (pivot point buy signals with protective sell stops under the day's low). These rules shift focus from entry timing to systematic stop management, directly embodying the exit-first mindset.

## Trading Implication

Traders should prioritize stop placement and trailing per their system's rules (e.g., adjust P&F stop to the latest column, place pivot point stops under the current low) rather than over-optimizing entries alone.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
