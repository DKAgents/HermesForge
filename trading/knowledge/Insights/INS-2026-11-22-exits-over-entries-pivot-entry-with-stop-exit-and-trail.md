---
type: insight
date: 2026-11-22
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
# Exits Over Entries: Pivot Entry with Stop Exit and Trail

## Discovery Summary

The seed insight that exits matter more than entries is embodied by the stop rules in EN071 Pivot Point Buy Signal Rules: the buy-stop trigger defines where to enter, while the protective sell stop below today's low/open is the exit that caps loss. C245 Stop Order explains that this protective sell stop is a stop order and can be trailed once profits accrue; RG023 P&F Trailing Stop Adjustment specifies how to trail using the latest o column. This gives a complete sequence: pivot-point entry, initial protective stop, then trailing stop to lock in profits.

## Trading Implication

When trading EN071 pivot-point buy signals, immediately place the protective sell stop under today's low/open, and after the position moves in your favor, trail it upward using the latest P&F o column per RG023 rather than leaving the stop static.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-10-exits-matter-trail-stops-after-pivot-point-buy-signals|Exits matter: trail stops after pivot-point buy signals]]
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
