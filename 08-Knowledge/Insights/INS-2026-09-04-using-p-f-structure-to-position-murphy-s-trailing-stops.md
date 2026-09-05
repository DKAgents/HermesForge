---
type: insight
date: 2026-09-04
actionability: 4
connection_type: reveals_sequence
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: Murphy - Technical Analysis of the Financial Markets
---
# Using P&F structure to position Murphy's trailing stops

## Discovery Summary

Murphy emphasizes that exits matter more than entries, and RG023 provides a specific P&F trailing stop method: raising stops to just below the latest O column in an uptrend or lowering to just above the latest X column in a downtrend. EN071 offers a pivot-point entry rule with protective stops under the current day's low, but its stop is static and day-bound. RG023's P&F technique reveals a sequence where after a pivot-point entry per EN071, the trader can transition from the initial day's-low stop to a structurally-defined P&F trailing stop that adjusts with each new column formation, staying with the trend longer.

## Trading Implication

After entering on an EN071 pivot-point buy signal, abandon the static intraday protective stop once a P&F chart shows a new O column in the uptrend, and shift to trailing the stop just below the most recent O column as described in RG023 to let trend profits accumulate.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
