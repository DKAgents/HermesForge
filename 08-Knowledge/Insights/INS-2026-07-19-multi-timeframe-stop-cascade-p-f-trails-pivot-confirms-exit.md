---
type: insight
date: 2026-07-19
actionability: 4
connection_type: reveals_sequence
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Multi-Timeframe Stop Cascade: P&F Trails, Pivot Confirms Exit

## Discovery Summary

RG023 defines a structural trailing stop method using P&F column lows/highs, while EN071 defines an intraday entry sequence with a same-day protective stop under the current day's low. C245 bridges both by clarifying that stops serve dual roles: loss limitation AND profit protection. The non-obvious connection is that EN071's intraday protective stop (below current day's low) can serve as the *initial* stop, while RG023's P&F trailing method governs stop management *after* the position matures — creating a two-phase exit framework where the exit discipline evolves from intraday tactical to multi-day structural.

## Trading Implication

On a pivot point buy signal per EN071, place the initial protective stop below the current day's low as specified; once the trade develops and a new P&F X-column forms per RG023, migrate the stop to just below the latest O-column, explicitly transitioning from entry-risk management to profit-protection mode.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
