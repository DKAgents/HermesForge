---
type: insight
date: 2026-08-15
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
# Trail Stops by Chart Structure, Not Price Distance

## Discovery Summary

RG023 defines WHERE to trail stops on P&F charts (below latest O-column in uptrend), C245 defines WHAT a stop order mechanically does (becomes market order at trigger), and EN071 defines WHEN to set stops relative to session events (below current day's low after buy stop election). Together they reveal a sequence: EN071 governs entry and initial stop placement intraday, C245 provides the execution mechanism, and RG023 provides the ongoing trailing logic as the trend extends. Murphy's exits-matter-more principle is operationalized by combining the P&F column-based trailing rule (RG023) with the pivot-point session rule's requirement that prices close above both prior close and today's open (EN071) — if that close condition fails, the P&F trailing stop acts as the exit trigger.

## Trading Implication

After a pivot-point buy signal is confirmed per EN071, trail the protective stop using RG023's rule — raise it to just below the latest O-column on the P&F chart rather than using a fixed-distance stop, ensuring the exit logic is anchored to chart structure and accumulated profit protection rather than arbitrary price levels.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5

## Related Notes
- [[C243-market-order|Market Order]]
- [[C245-stop-order|Stop Order]]
