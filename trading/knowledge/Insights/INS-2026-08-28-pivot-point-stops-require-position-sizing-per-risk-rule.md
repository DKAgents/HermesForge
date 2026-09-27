---
type: insight
date: 2026-08-28
actionability: 4
connection_type: adds_condition
domains: [concepts, risk_guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Pivot Point Stops Require Position Sizing Per Risk Rule

## Discovery Summary

EN071 pivot-point-buy-signal-rules defines exact protective stop levels (below the day's low or below the opening price) but gives no guidance on capital allocation. RG035 specifies that stops must sit at technical levels and that position size must adjust inversely to stop distance to respect a maximum risk budget (e.g., 5% of account). The pivot point rule's technical stops therefore act as inputs to the money-management rule: the wider the required stop, the smaller the allowable position.

## Trading Implication

When a pivot-point buy signal fires, measure the distance to the protective stop dictated by EN071, then use the formula from RG035 to size the trade so dollar risk stays within your per-trade limit.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**adds_condition** — Actionability score: 4/5
