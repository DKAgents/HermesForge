---
type: insight
date: 2026-11-25
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk_guidelines, rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "EN069-price-gaps-as-support-and-resistance-for-timing"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Old support and gap levels set stops, driving position size

## Discovery Summary

C065 says violated support in a downtrend becomes resistance, giving a short-entry trigger at that ceiling with a stop above. EN069 says gaps after an upmove act as support, giving a long-entry trigger on a dip into the gap with a stop below. Together, Murphy's S/R rules define a clear stop distance for both long and short sides, and that distance is what determines position size once the trader sets a fixed risk amount.

## Trading Implication

Before taking a short in a downtrend, place the stop above the old support/resistance level; before buying a gap pullback, place the stop below the gap. Size the position so the distance from entry to stop equals your predetermined dollar risk.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
