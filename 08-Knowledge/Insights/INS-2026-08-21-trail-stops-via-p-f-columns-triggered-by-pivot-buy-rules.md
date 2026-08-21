---
type: insight
date: 2026-08-21
actionability: 4
connection_type: reveals_sequence
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Trail Stops via P&F Columns, Triggered by Pivot Buy Rules

## Discovery Summary

EN071 defines entry via pivot point buy stops with an immediate protective sell stop below the current day's low — establishing that the exit rule is embedded in the entry process. Once in a trend with repeat signals, RG023 provides a systematic trailing mechanism: raise the stop to just below the latest O column in P&F charts, operationalizing Murphy's principle that exits matter more than entries. C245 clarifies that these stops become market orders on trigger, meaning the P&F trailing stop level from RG023 should account for potential slippage in fast markets.

## Trading Implication

After a pivot point buy signal (EN071) initiates a long, transition from the initial day's-low stop to a P&F trailing stop (RG023) as the trend extends — specifically trail to just below the latest O column — and size that stop buffer wider than the nominal level to account for fast-market slippage per C245.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
