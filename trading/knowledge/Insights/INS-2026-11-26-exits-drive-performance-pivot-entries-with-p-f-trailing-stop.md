---
type: insight
date: 2026-11-26
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
# Exits drive performance: Pivot entries with P&F trailing stops

## Discovery Summary

EN071 provides a precise entry trigger using pivot points with an initial protective stop. However, Murphy's insight (referenced in C245) emphasizes that exits matter more than entries. RG023 offers a method to trail stops using P&F columns, which transforms a static entry stop into a dynamic profit-protecting exit. Combining these reveals a systematic sequence: enter on pivot point signals, then immediately manage the exit with P&F trailing stops to capture trends.

## Trading Implication

After executing a pivot point buy signal per EN071, do not keep the initial stop static. Instead, apply the P&F trailing stop rule (raise stop to just below the latest o column) to protect profits and let winners run.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
