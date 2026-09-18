---
type: insight
date: 2026-09-17
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Stop placement reinforces exit priority over entry

## Discovery Summary

Murphy's insight that exits matter more than entries is directly implemented in RG023's P&F trailing stop adjustment and C245's stop order logic. The pivot point rules in EN071 prioritize entry triggers but then mandate a protective stop below the day's low, showing that even systematic entry rules depend on stop placement for profit protection. The common thread is that the stop exit (trailing or fixed) defines the risk-reward outcome, not the entry signal.

## Trading Implication

When designing any strategy, first define the stop-exit logic (trailing or fixed) and only then select an entry rule; the exit determines whether the trade preserves capital and locks in profits.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
