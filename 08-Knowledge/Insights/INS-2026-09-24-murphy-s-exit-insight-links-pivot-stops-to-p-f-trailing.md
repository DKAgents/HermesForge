---
type: insight
date: 2026-09-24
actionability: 3
connection_type: adds_condition
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: Murphy - Technical Analysis of the Financial Markets
---
# Murphy's exit insight links pivot stops to P&F trailing

## Discovery Summary

Murphy's insight (C245) that exits matter more than entries is exemplified by both the pivot point buy signal rules (EN071) and the P&F trailing stop adjustment (RG023). The pivot rules specify an initial protective stop below the current day's low, but do not address trailing. Incorporating the P&F trailing stop method—raising the stop to just below the latest o column in an uptrend—adds a dynamic condition to protect profits after a pivot breakout, directly applying Murphy's principle.

## Trading Implication

After entering on a pivot point buy signal, trail the protective stop using the P&F method: raise it to just below the most recent o column as the uptrend continues, rather than keeping a static stop.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 3/5
