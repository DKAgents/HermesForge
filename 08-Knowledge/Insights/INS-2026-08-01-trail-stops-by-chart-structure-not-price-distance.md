---
type: insight
date: 2026-08-01
actionability: 4
connection_type: reveals_sequence
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Trail Stops by Chart Structure, Not Price Distance

## Discovery Summary

The three notes together create a complete exit framework: EN071 establishes the initial protective stop at the current day's low after entry, C245 confirms stops should be trailed upward to protect profits, and RG023 specifies exactly HOW to trail on P&F charts — below the latest O column in uptrends. The non-obvious connection is that EN071's intraday pivot entry rule generates a precise initial stop anchor (today's low), which can then be graduated into the P&F trailing method from RG023 as the trend matures, creating a structured lifecycle for stop management rather than arbitrary price-distance trailing.

## Trading Implication

After a pivot point buy signal from EN071 is triggered, use the current day's low as the initial stop per EN071 rules, then transition to trailing below the latest O column per RG023 once the position shows profit and a P&F chart confirms the trend — exit methodology evolves with the trade's maturity.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
