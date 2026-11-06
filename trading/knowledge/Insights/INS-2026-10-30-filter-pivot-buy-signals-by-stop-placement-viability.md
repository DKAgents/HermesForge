---
type: insight
date: 2026-10-30
actionability: 4
connection_type: creates_filter
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Filter pivot buy signals by stop placement viability

## Discovery Summary

Murphy's principle that exits matter more than entries turns RG023-pf-trailing-stop-adjustment into the primary performance driver, while EN071-pivot-point-buy-signal-rules only locates an opportunity. C245-stop-order is the tool that makes such exits explicit. Thus an entry should be accepted only if a defined stop order and a trailing-stop adjustment plan can be specified before the pivot signal is taken.

## Trading Implication

Before executing an EN071 pivot-point buy signal, define and place the C245 stop order and RG023 trailing-stop plan; if no workable stop placement exists, skip the entry.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C245-stop-order|Stop Order]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
