---
type: insight
date: 2026-09-28
actionability: 4
connection_type: contradicts_assumption
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Exit-first stop placement overrides entry signals

## Discovery Summary

Murphy's insight that exits matter more than entries suggests that entry signals like EN071-pivot-point-buy-signal-rules should be subordinate to exit planning. The RG023-pf-trailing-stop-adjustment rule emphasizes that trailing stops must be adjusted based on price action (e.g., pivot points), which aligns with placing stops at key levels rather than merely at entry-triggered points. The C245-stop-order concept reinforces that a stop is an executable order, and its placement should be derived from exit logic (e.g., below pivot support), not from the entry signal itself. This contradicts the naive assumption that a buy signal dictates where to place the stop.

## Trading Implication

Before acting on any pivot-point buy signal, first define the stop level using pivot-based trailing stop rules (RG023) and place a stop order (C245) at that level. If the stop distance is too wide relative to risk, skip the trade regardless of the entry signal strength.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**contradicts_assumption** — Actionability score: 4/5
