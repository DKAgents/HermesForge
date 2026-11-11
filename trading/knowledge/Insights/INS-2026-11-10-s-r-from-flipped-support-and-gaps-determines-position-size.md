---
type: insight
date: 2026-11-10
actionability: 4
connection_type: confirms_risk_rule
domains: [position_sizing, price_gaps, risk_management, support_and_resistance, trading_rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "EN069-price-gaps-as-support-and-resistance-for-timing"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# S/R from flipped support and gaps determines position size

## Discovery Summary

C065 (previous support as future resistance in downtrend) identifies a short-entry zone on bounces into old support, with a natural stop above that level. EN069 (price gaps as support and resistance for timing) identifies long/short entry zones at gaps and explicitly places protective stops beyond the gap. Both are Murphy S/R rules, and the distance from entry to stop defines risk per share, which then determines position size for a fixed risk budget.

## Trading Implication

In a downtrend, sell bounces into former support now acting as resistance, stopping above it; in an uptrend, buy dips into underlying gaps, stopping below them. Size every position so the entry-to-stop distance represents your predefined per-trade risk.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
