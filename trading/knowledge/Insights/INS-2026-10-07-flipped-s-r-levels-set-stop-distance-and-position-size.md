---
type: insight
date: 2026-10-07
actionability: 4
connection_type: confirms_risk_rule
domains: [position_sizing, risk_management, support_resistance, trend_following]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "C065-previous-support-as-future-resistance-in-downtrend", "C064-previous-peaks-as-future-support-in-uptrend"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
---

# Flipped S/R levels set stop distance and position size

## Discovery Summary

C064 and C065 show the same role-reversal principle in both uptrends and downtrends: broken resistance becomes support, and broken support becomes resistance. These flipped levels give objective stop-placement points, so the distance from entry to the flip level defines initial risk per share. Position size can then be computed as account risk divided by that per-share risk. Murphy's rules on both sides therefore directly support the risk rule that stop distance determines position size.

## Trading Implication

In an uptrend, place protective stops below broken resistance now acting as support; in a downtrend, place stops above broken support now acting as resistance. Size each position so the distance to that flipped level respects your account risk target.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[C064-previous-peaks-as-future-support-in-uptrend]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
