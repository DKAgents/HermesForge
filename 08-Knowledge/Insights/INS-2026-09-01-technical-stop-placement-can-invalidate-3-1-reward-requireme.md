---
type: insight
date: 2026-09-01
actionability: 4
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
# Technical stop placement can invalidate 3:1 reward requirement

## Discovery Summary

The pivot point buy signal rules in EN071 require a protective stop below the current day's low (or open), which is a purely technical placement. However, RG035 mandates stops satisfy both technical and money management criteria, including a maximum risk limit. When the technical stop distance from entry exceeds one-third of the profit target distance, the 3:1 reward/risk ratio is violated, forcing a choice between skipping the trade or reducing position size per RG035's rule that looser stops require smaller positions.

## Trading Implication

Before entering any pivot point breakout trade, calculate whether the technical stop distance allows at least a 3:1 reward/risk ratio relative to your target; if not, either pass on the trade or reduce position size according to money management limits, but never move the stop inside a valid technical level just to satisfy the ratio.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**creates_filter** — Actionability score: 4/5
