---
type: insight
date: 2026-11-11
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
# Role-reversed S/R and gap levels determine stop distance and size

## Discovery Summary

C065 (Murphy p.83) says violated support in a downtrend becomes resistance on subsequent bounces, creating a shorting zone. EN069 adds that in bear moves traders should sell rallies into the lower edge of a gap and keep protective stops above the gap; combined with the seed principle, the distance from entry to that stop is the per-unit risk that sets position size. These are two sides of the same Murphy S/R logic: identify the level, place the stop beyond it, and size off the distance.

## Trading Implication

When shorting a downtrend bounce at prior support turned resistance or at gap resistance, set the stop just above the level and divide the allowed risk per trade by that stop distance to size the position. Mirror the approach for long entries at gap support.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
