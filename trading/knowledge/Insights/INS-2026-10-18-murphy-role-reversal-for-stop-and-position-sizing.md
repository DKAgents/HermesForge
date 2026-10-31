---
type: insight
date: 2026-10-18
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk_guidelines]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "C065-previous-support-as-future-resistance-in-downtrend", "C064-previous-peaks-as-future-support-in-uptrend"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: Murphy - Technical Analysis of the Financial Markets
---
# Murphy role reversal for stop and position sizing

## Discovery Summary

The Murphy rules of previous support becoming resistance in downtrend (C065) and previous peaks becoming support in uptrend (C064) provide precise levels for stop loss placement. The seed question explicitly links these levels to stop distance, which directly determines position size via a fixed fraction risk model. Together, they confirm a risk guideline: use flipped support/resistance levels to set stops and calculate position size.

## Trading Implication

For long trades in an uptrend, place stop loss just below the prior peak that now acts as support; for short trades in a downtrend, place stop loss just above the prior support that now acts as resistance. Use the distance from entry to stop to compute position size based on a fixed maximum loss per trade.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[C064-previous-peaks-as-future-support-in-uptrend]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[C334-resistance-level|Resistance Level]]
