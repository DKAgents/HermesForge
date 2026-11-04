---
type: insight
date: 2026-11-03
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
# Trail Stops After Pivot Buy Signals: Exits Beat Entries

## Discovery Summary

EN071-pivot-point-buy-signal-rules specifies the entry and initial protective stop but does not address subsequent trade management. RG023-pf-trailing-stop-adjustment supplies the missing exit-management rule: after repeat buy signals, raise the sell stop to just below the latest o column to protect accumulated profits. C245-stop-order confirms that a protective stop can be trailed and warns that fills may be worse than the stop in fast markets. Together they implement the Murphy principle that exits matter more than entries: entry only opens the position; the trailing-stop sequence decides the outcome.

## Trading Implication

After a pivot-point buy stop is elected, place the initial protective sell stop below the day's low; once the trend produces repeat buy signals, trail that stop up to just below the latest P&F o column rather than holding the original stop.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
