---
type: insight
date: 2026-11-15
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, trading-rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Exits Matter: Structure-Based Stop Placement Aligns with Murphy

## Discovery Summary

Murphy's dictum that exits matter more than entries is operationalized by C245-stop-order, EN071-pivot-point-buy-signal-rules, and RG023-pf-trailing-stop-adjustment. C245 notes sell stops can be trailed upward to protect profits; EN071 makes a protective sell stop part of the entry rule; RG023 gives the trailing anchor: below the latest o column in an uptrend. Exits are therefore not an afterthought but a structural risk decision tied to the same price action that generated the signal.

## Trading Implication

For every long taken on a pivot or P&F signal, place a sell stop below the trade's structural support (current day's low/open, latest o column) and trail it upward as the trend produces repeat signals; do not let exit management be looser than entry selection.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
