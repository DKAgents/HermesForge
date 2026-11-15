---
type: insight
date: 2026-11-14
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk_guidelines, trading_rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "EN069-price-gaps-as-support-and-resistance-for-timing"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# S/R Levels Set Stop Distance and Position Size

## Discovery Summary

C065 and EN069 both identify concrete chart levels—previous support flipped to resistance in downtrends, and price gaps—that define where protective stops belong. These Murphy-derived levels make the risk rule actionable: stop distance is set by the distance to the violated support or gap, and position size follows from that distance. Together they give a repeatable method for both long and short entries with defined invalidation points.

## Trading Implication

Before entering, mark the nearest prior-support-as-resistance or gap edge, place the stop beyond it, and size the position so the dollar risk from entry to stop fits the account risk budget.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
