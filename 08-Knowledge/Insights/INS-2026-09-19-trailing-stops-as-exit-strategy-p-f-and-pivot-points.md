---
type: insight
date: 2026-09-19
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Trailing Stops as Exit Strategy: P&F and Pivot Points

## Discovery Summary

Murphy's emphasis on exits is operationalized in RG023's P&F trailing stop (raising stop below each o-column) and EN071's pivot point buy signal (placing protective sell stop under current day's low). Both confirm that stop placement is not arbitrary but tied to structural price levels (P&F columns or pivot highs/lows), and that exiting/trailing is as critical as entry timing. C245's stop order mechanism underpins both, showing how stop orders are the execution vehicle for these risk rules.

## Trading Implication

Traders should prioritize systematic stop placement—using P&F column structure or pivot day's low—and trail stops proactively to lock in profits, rather than focusing solely on entry signals. This aligns with Murphy's dictum that exits matter more.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
