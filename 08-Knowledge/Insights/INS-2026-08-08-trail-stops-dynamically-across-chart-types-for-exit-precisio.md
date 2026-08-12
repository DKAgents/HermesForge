---
type: insight
date: 2026-08-08
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
# Trail Stops Dynamically Across Chart Types for Exit Precision

## Discovery Summary

The three notes collectively reveal a layered exit framework: EN071 establishes entry-specific initial stop placement (below current day's low on pivot buy signals), C245 establishes the mechanical execution mechanism (sell stop becomes market order at trigger), and RG023 provides the ongoing trailing logic (raise stop below latest O column in P&F uptrend). Together they form a complete lifecycle: set initial stop on entry per EN071, execute via stop order per C245, then trail using P&F column logic per RG023 as the trend extends. This sequence directly answers Murphy's insight that exits matter more — the entry rules are finite, but the trailing stop rules govern how much profit is ultimately captured.

## Trading Implication

Once a pivot-point buy is triggered and initial stop is set below the day's low, the trader should switch to P&F trailing methodology — raising the protective sell stop to just below the latest O column — rather than holding a static stop, to both protect accumulated gains and stay in the trend.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
