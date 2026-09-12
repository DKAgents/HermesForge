---
type: insight
date: 2026-09-12
actionability: 4
connection_type: adds_condition
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# P&F Trailing Stops Complete Pivot Point Entry Rules

## Discovery Summary

Murphy's assertion that exits matter more than entries (C245) is put into practice by RG023's P&F trailing stop method, which adjusts stops under each new O column in an uptrend. EN071's pivot point buy rules specify only an initial protective stop under the entry day's low, lacking any exit management thereafter. The connection is that RG023 supplies the missing post-entry exit discipline, allowing a trader to protect accumulated profits in a systematic way that aligns with Murphy's principle.

## Trading Implication

When a pivot point breakout entry is triggered (per EN071), replace the static initial stop with a P&F-based trailing stop, raising it beneath each subsequent O column to capture extended trend profits.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 4/5
