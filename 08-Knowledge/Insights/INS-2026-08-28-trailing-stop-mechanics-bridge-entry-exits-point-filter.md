---
type: insight
date: 2026-08-28
actionability: 4
connection_type: adds_condition
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Trailing stop mechanics bridge entry exits point-filter

## Discovery Summary

RG023-pf-trailing-stop-adjustment provides a mechanical method for profit protection by trailing stops below O-columns in uptrends, answering Murphy's emphasis (cited in C245-stop-order) that exits matter more than entries. EN071-pivot-point-buy-signal-rules demonstrates entry-specific stop placement but lacks ongoing adjustment rules — applying RG023's P&F column logic after EN071's entry would create a complete lifecycle stop strategy. The connection reveals that EN071's initial protective stop placement could be replaced or supplemented by the P&F column trailing method once price develops sufficient swing structure, turning a static entry-stop rule into a dynamic profit-protection mechanism.

## Trading Implication

After entering on an EN071 pivot-point buy signal, switch from the initial below-day's-low stop to trailing stops below each newly formed P&F O-column as the uptrend progresses, rather than keeping the static stop.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 4/5
