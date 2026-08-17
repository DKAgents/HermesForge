---
type: insight
date: 2026-08-17
actionability: 4
connection_type: reveals_sequence
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Multi-Timeframe Stop Sequencing: Entry Trigger Then Trail via P&F

## Discovery Summary

EN071 defines a precise entry protocol using buy stops above prior-day highs with an immediate protective sell stop below the current day's low — this satisfies the entry/initial-stop phase. C245 confirms that sell stops can be 'trailed upward to protect profits' once a position is established. RG023 then provides the specific trailing mechanism: once repeat buy signals appear on a P&F chart, the stop is raised to just below the latest O column. Together these three notes form a sequential exit management system: (1) set initial stop at current day's low per EN071, (2) trail upward as price advances per C245, (3) anchor the trail to P&F O-column lows per RG023.

## Trading Implication

After a pivot-point buy signal is elected per EN071, a trader should immediately place the initial stop below the current day's low, then switch to the P&F trailing stop rule (RG023) once a repeat buy signal appears on the P&F chart, raising the stop to just below the latest O column to lock in accumulated profits.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
