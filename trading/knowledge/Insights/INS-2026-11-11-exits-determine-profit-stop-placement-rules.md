---
type: insight
date: 2026-11-11
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
# Exits Determine Profit: Stop Placement Rules

## Discovery Summary

Murphy's insight (C245) emphasizes that stop orders are 'strongly recommended to limit losses and protect profits,' which aligns with RG023's trailing stop technique using P&F columns and EN071's specific protective stop placements for pivot point breakouts. This connection shows that stop placement is not arbitrary but based on technical structure, reinforcing that exits are as critical as entries.

## Trading Implication

Use technical levels (e.g., P&F columns, pivot point lows) to set initial stops, and trail them as trends continue, rather than using random or fixed percentage stops.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
