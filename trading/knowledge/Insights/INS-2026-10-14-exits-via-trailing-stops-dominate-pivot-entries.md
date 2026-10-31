---
type: insight
date: 2026-10-14
actionability: 3
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Exits via trailing stops dominate pivot entries

## Discovery Summary

Murphy's principle that exits matter more than entries directly supports RG023-pf-trailing-stop-adjustment and elevates it above the exact entry details in EN071-pivot-point-buy-signal-rules. The C245-stop-order is the practical mechanism that enforces that exit logic. Thus, a pivot-point buy signal should be considered incomplete until a stop and trailing-adjustment plan is attached.

## Trading Implication

After any EN071 pivot-point buy signal, immediately place a C245 stop order and apply RG023 trailing-stop adjustment; evaluate the trade by how well the exit is managed rather than by entry precision.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 3/5

## Related Notes
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
- [[C245-stop-order|Stop Order]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
