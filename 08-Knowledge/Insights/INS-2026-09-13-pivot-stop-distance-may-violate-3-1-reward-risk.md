---
type: insight
date: 2026-09-13
actionability: 3
connection_type: creates_filter
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Pivot stop distance may violate 3:1 reward/risk

## Discovery Summary

The pivot point buy signal rules (EN071) place a protective stop at a technical level (below current day's low or open), satisfying RG035's requirement that stops must be at valid technical levels. However, that stop distance often creates a risk per share that, when scaled to a 3:1 reward/risk target, may push the profit objective beyond any nearby technical resistance, making the ratio unachievable. Traders can filter entries by first verifying that a 3:1 multiple of the pivot rule's stop distance lands at a plausible technical target.

## Trading Implication

Before executing a pivot point buy stop entry, compute the stop distance, project a 3:1 profit target, and only take the trade if that target coincides with a realistic resistance level; otherwise skip it.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**creates_filter** — Actionability score: 3/5
