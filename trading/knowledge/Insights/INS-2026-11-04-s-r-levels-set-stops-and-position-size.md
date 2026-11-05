---
type: insight
date: 2026-11-04
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk management, rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "EN069-price-gaps-as-support-and-resistance-for-timing"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# S/R Levels Set Stops and Position Size

## Discovery Summary

C065 (Previous Support as Future Resistance) and EN069 (Price Gaps as Support/Resistance) both provide precise price levels that define stop placement. In a downtrend, a short can place its stop above the old support (now resistance); in an uptrend, a long can place its stop below the gap. These exact stop distances, as noted in the seed question, directly determine position size when using a fixed risk-per-trade model. The two rules together create a complete workflow: identify S/R from chart patterns or gaps, set the stop accordingly, then size the position based on the stop distance.

## Trading Implication

When shorting in a downtrend, set the stop just above the prior support (now resistance) or the upper edge of a gap; when buying in an uptrend, set the stop just below the gap. Then calculate position size by dividing the risk per trade by the stop distance.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
