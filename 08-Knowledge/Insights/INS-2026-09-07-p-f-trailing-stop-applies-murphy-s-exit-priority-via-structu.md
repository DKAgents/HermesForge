---
type: insight
date: 2026-09-07
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: Murphy - Technical Analysis of the Financial Markets
---
# P&F trailing stop applies Murphy's exit priority via structure

## Discovery Summary

Murphy's focus on exits over entries is operationally embedded in RG023-pf-trailing-stop-adjustment: the stop is systematically raised below the latest O-column in an uptrend, making exit logic structural rather than discretionary. This directly parallels EN071-pivot-point-buy-signal-rules, where a protective sell stop is placed below the current day's low immediately upon entry, ensuring the exit is defined before the trade develops. C245-stop-order defines the mechanism for both — the stop order becomes a market order when hit, closing the loop on Murphy's exit-first philosophy.

## Trading Implication

Trail stops using the specific structural anchor of the latest O-column in P&F uptrends rather than arbitrary percentages; define the protective stop level before or at entry as EN071 does with today's low.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
