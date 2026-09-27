---
type: insight
date: 2026-08-22
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
# Multi-Method Stop Trailing Creates Layered Exit Protocol

## Discovery Summary

RG023 provides a structural trailing stop rule using P&F column lows/highs, while EN071 provides an intraday entry-triggered stop (below current day's low after buy stop election). C245 confirms stops should be trailed upward to protect profits. The non-obvious connection is that EN071's intraday protective stop (below current day's low) serves as the INITIAL stop at entry, while RG023's P&F trailing method provides the CONTINUATION stop mechanism once a trend develops — creating a sequenced two-phase exit protocol rather than a single static stop.

## Trading Implication

After a pivot point buy signal is elected per EN071 rules, place the initial protective sell stop below the current day's low; once the position matures and repeat P&F buy signals appear, transition to trailing the stop just below the latest O column per RG023, graduating from intraday to structural stop logic.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5

## Related Notes
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
