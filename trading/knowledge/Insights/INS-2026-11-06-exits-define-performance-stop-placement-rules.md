---
type: insight
date: 2026-11-06
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
# Exits Define Performance: Stop Placement Rules

## Discovery Summary

Murphy's insight that exits matter more than entries is operationalized through stop orders. C245-stop-order defines the mechanics of stop placement, RG023-pf-trailing-stop-adjustment provides a systematic trailing method based on P&F columns, and EN071-pivot-point-buy-signal-rules specifies exact protective stop levels (below day's low or open). These rules collectively show that exit discipline is embedded in the entry plan, not an afterthought.

## Trading Implication

Traders should predefine stop levels using techniques like P&F trailing stops or pivot point extremes, treating exits as the primary risk management decision rather than improvising after entry.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
