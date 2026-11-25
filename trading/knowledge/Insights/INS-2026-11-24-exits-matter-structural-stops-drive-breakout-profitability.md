---
type: insight
date: 2026-11-24
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
# Exits matter: structural stops drive breakout profitability

## Discovery Summary

Murphy's insight that exits matter more than entries is operationalized by pairing every entry-triggering stop order with a structural protective stop. The Pivot Point Buy Signal Rules define entry via a buy stop above prior/current highs but explicitly require a protective sell stop below the current day's low or today's open. The P&F Trailing Stop Adjustment then shows how to trail that stop below each new o column in an uptrend, while the Stop Order concept confirms stops are strongly recommended to limit losses and protect profits.

## Trading Implication

Before entering any breakout, define the protective stop using current structure — below the current day's low/open for pivot entries or below the latest P&F o column — and trail it as the trend produces new signals. Do not treat the entry signal as the trade; the stop placement and subsequent adjustment determine profitability.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-27-exits-matter-more-stop-placement-rules-edge|Exits matter more: stop placement rules edge]]
