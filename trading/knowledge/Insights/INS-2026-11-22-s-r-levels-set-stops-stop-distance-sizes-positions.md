---
type: insight
date: 2026-11-22
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
# S/R levels set stops; stop distance sizes positions

## Discovery Summary

In a downtrend, C065 says violated support flips to resistance and can be sold on rallies. EN069 similarly says a bear-market gap can be sold on a rally into it with a stop above the gap. Both are Murphy-based S/R levels, so they define the invalidation point: the stop is placed beyond the relevant level. Since stop distance in price units determines how much can be traded for a fixed risk budget, these chart concepts feed directly into position sizing.

## Trading Implication

For any short entry at former support-turned-resistance or a bearish gap, place the protective stop just above the S/R level and size the position as allowed risk divided by that stop distance. Avoid arbitrary stops; let the identified S/R level set the risk.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
