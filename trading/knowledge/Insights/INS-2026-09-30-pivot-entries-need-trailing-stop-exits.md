---
type: insight
date: 2026-09-30
actionability: 3
connection_type: reveals_sequence
domains: [indicators, risk management, trading rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Pivot entries need trailing stop exits

## Discovery Summary

EN071 defines pivot point buy signals, which are entry-focused. RG023 provides trailing stop adjustment guidelines for managing exits. Murphy's insight that exits matter more than entries suggests that the pivot buy signal should be immediately followed by a trailing stop rule (C245) to lock profits and limit losses, rather than relying solely on the entry signal for performance.

## Trading Implication

When executing a pivot point buy signal from EN071, immediately apply a trailing stop adjustment per RG023 to actively manage the exit, prioritizing stop placement over the entry signal's initial promise.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 3/5
