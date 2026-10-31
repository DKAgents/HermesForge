---
type: insight
date: 2026-10-30
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk guidelines, trading rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "C065-previous-support-as-future-resistance-in-downtrend", "C064-previous-peaks-as-future-support-in-uptrend"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Flipped S/R sets stops and position size

## Discovery Summary

C065 and C064 formalize Murphy's S/R reversal rule: violated support becomes resistance in downtrends, and prior peaks become support in uptrends. That gives an objective stop-loss level on both sides of a trade. The seed question completes the insight: the distance from entry to that flipped level is the stop distance, which directly determines position size.

## Trading Implication

In an uptrend, place stops below prior peaks now acting as support; in a downtrend, place stops above violated support now acting as resistance. Size each position so the per-unit stop distance equals the amount of risk you are willing to take.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[C064-previous-peaks-as-future-support-in-uptrend]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
