---
type: insight
date: 2026-08-30
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Exits prioritized via dynamic stop placement rules

## Discovery Summary

Murphy’s emphasis on exit importance (C245) is operationalized by the P&F trailing stop rule (RG023) that raises stops below the latest o-column in an uptrend, and the pivot point rule (EN071) that immediately places a protective sell stop below the current day’s low upon entry. Both rules treat the exit as the dynamic, non-negotiable component of the trade, not an afterthought.

## Trading Implication

Traders should always combine any entry signal with a pre-planned protective stop and then trail that stop using specific technical levels—such as the most recent P&F column or intraday pivot lows—rather than relying on discretionary or fixed-point exits.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
