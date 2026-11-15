---
type: insight
date: 2026-11-14
actionability: 4
connection_type: reveals_sequence
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# P&F trailing stop transforms pivot entries into managed exits

## Discovery Summary

EN071-pivot-point-buy-signal-rules provides an entry trigger and an initial protective stop, but no exit trail. RG023-pf-trailing-stop-adjustment supplies the missing exit logic: once the pivot buy stop is elected, trail the protective sell stop up to just below the latest o column. This operationalizes Murphy's insight that exits matter more than entries by making profit protection rule-based rather than discretionary.

## Trading Implication

After a pivot point buy stop is filled, do not rely only on the initial protective stop; trail it upward using the P&F column structure to lock in gains as the trend continues.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
