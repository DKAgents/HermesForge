---
type: insight
date: 2026-09-25
actionability: 4
connection_type: adds_condition
domains: [concepts, risk-guidelines, rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "EN069-price-gaps-as-support-and-resistance-for-timing", "RG035-combining-technical-factors-with-money-management-for-stop-p"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
---

# Murphy S/R levels determine stop distance and position size

## Discovery Summary

C065 and EN069 provide specific technical levels (violated support as resistance in downtrends, price gap boundaries) that serve as valid stop placement points. RG035 mandates that protective stops must be at such technical levels and that stop distance directly controls position size under a fixed risk limit. Together, they create a concrete workflow: identify the S/R level from Murphy's rules, set the stop just beyond it, then compute position size using the stop distance and a predefined maximum loss per trade.

## Trading Implication

Use C065's broken support (now resistance) or EN069's gap edges as the reference for stop placement, then adjust position size so that the stop distance multiplied by position value does not exceed your fixed risk per trade (e.g., 5% of account).

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]

## Connection Type

**adds_condition** — Actionability score: 4/5
