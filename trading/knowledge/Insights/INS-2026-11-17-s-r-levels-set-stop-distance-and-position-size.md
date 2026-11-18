---
type: insight
date: 2026-11-17
actionability: 4
connection_type: adds_condition
domains: [concepts, risk_guidelines, rules]
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

C065 identifies violated prior support as resistance on bounces in downtrends, specifying a short-entry zone with a stop above that level. EN069 identifies gap support after upmoves and gap resistance in bear moves, specifying buy/sell zones with stops beyond the gap. Both rules transform S/R levels into objective stop distances, and stop distance is the denominator for position sizing given fixed risk. Together they cover both long and short timing with clear risk placement.

## Trading Implication

Before entering, locate the nearest S/R level that applies to the current side (prior support/resistance for shorts, gap support for longs) and place the protective stop beyond it. Then size the position so the stop distance represents the predetermined account risk.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]

## Connection Type

**adds_condition** — Actionability score: 4/5
