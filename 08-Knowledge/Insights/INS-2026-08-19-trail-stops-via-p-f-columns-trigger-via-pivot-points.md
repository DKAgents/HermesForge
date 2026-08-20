---
type: insight
date: 2026-08-19
actionability: 4
connection_type: reveals_sequence
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Trail Stops Via P&F Columns, Trigger Via Pivot Points

## Discovery Summary

The three notes form a complete exit-centric trading system: EN071 defines the entry trigger (buy stop above prior high with initial protective stop below current day's low), C245 confirms stops must be placed immediately at entry and can be trailed, and RG023 provides the specific trailing mechanism — once a P&F trend continues with repeat buy signals, trail the stop to just below the latest O column. Murphy's insight that exits matter more than entries is operationalized by replacing the arbitrary initial stop from EN071 with a P&F-column-defined trailing stop that adapts to trend structure rather than intraday noise.

## Trading Implication

After a pivot point buy signal is triggered (EN071), place the initial protective sell stop below the current day's low (C245), then convert to a P&F trailing stop (RG023) — raising it to just below the latest O column as each new repeat buy signal appears, ensuring profit protection scales with trend progression rather than remaining fixed at the entry-day low.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
