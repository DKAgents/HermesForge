---
type: insight
date: 2026-11-19
actionability: 4
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
# Exits matter: structure-based stop placement protects profits

## Discovery Summary

C245-stop-order quotes Murphy that stop prices are strongly recommended to limit losses and protect profits, reinforcing that exits matter more than entries. EN071-pivot-point-buy-signal-rules provides exact entry buy-stop placement but then requires protective sell stops below the day's low or open. RG023-pf-trailing-stop-adjustment then shows how to trail that protective stop as the trend extends, using the latest P&F column. Together, they confirm that stop placement is the operational core of a trade: the entry signal only gets you in, while the exit stop determines whether you keep profits.

## Trading Implication

Traders should implement EN071's buy-stop entry only with an immediate protective sell stop below the day's low/open, and once the trade moves in their favor, trail that stop using RG023's P&F column method instead of leaving the exit to discretion.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
- [[RG020-protective-sell-stops-on-point-and-figure-charts|Protective Sell Stops on Point and Figure Charts]]
