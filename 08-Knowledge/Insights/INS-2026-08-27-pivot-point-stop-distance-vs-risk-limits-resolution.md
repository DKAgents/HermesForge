---
type: insight
date: 2026-08-27
actionability: 4
connection_type: resolves_conflict
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Pivot Point Stop Distance vs. Risk Limits Resolution

## Discovery Summary

The pivot point buy signal rules from EN071 require a protective sell stop below the current day's low, which may be far from the entry buy stop above the previous day's high. This stop distance can conflict with the money management rule in RG035 that limits total position risk to 5% of capital. RG035 resolves this by stating that a looser stop must reduce position size, so the trader must calculate position size based on the dollar risk from the pivot point stop distance to stay within the 5% limit.

## Trading Implication

Before entering a pivot point buy signal, measure the distance from the entry stop to the protective stop, limit dollar risk per trade to 5% of account equity, and size the position accordingly—even if the pivot point rules suggest a fixed stop level.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5
