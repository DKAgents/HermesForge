---
type: insight
date: 2026-11-04
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, pivot-points, point-and-figure, risk-guidelines, trading-rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Exits Matter: Pivot Entries Demand Immediate and Trailable Stops

## Discovery Summary

EN071 pivot-point buy-signal rules define precise entry triggers, but immediately require a protective sell stop below today's low or open, reflecting Murphy's insight that exits determine outcomes. RG023 P&F trailing stop adjustment extends this principle by systematically raising stops below the latest o column in uptrends, protecting profits after the entry is active. C245 stop-order mechanics supplies the execution tool that makes both protective and trailing exits concrete. The non-obvious connection is that an entry signal like EN071 is incomplete without the complementary exit rules from RG023 and the stop-order mechanics from C245.

## Trading Implication

Traders should treat every pivot-point entry as an exit-management trigger: place the EN071 protective sell stop immediately, then trail it with the P&F o-column method per RG023 as the trade moves in their favor.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
