---
type: insight
date: 2026-10-11
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
# Exits Over Entries: Trailing Stops After Pivot Signals

## Discovery Summary

EN071-pivot-point-buy-signal-rules provides the entry trigger, but Murphy's insight that exits matter more than entries shifts focus to the stop placement. C245-stop-order defines the initial exit mechanism, while RG023-pf-trailing-stop-adjustment governs how that stop is moved to lock in gains. The connection is sequential: execute the pivot signal, then actively manage the trailing stop as the higher-impact step.

## Trading Implication

After a pivot-point buy signal, prioritize placing and adjusting the stop order per RG023 trailing-stop rules rather than refining entry timing. The stop/exit management is what determines realized performance.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
- [[C245-stop-order|Stop Order]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
