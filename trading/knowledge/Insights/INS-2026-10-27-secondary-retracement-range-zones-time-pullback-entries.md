---
type: insight
date: 2026-10-27
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, rules]
sources: ["C050-secondary-trend-retracement-range", "EN068-4060-retracement-zones-for-timing-entries"]
seed_id: swing_low_entry_filter
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Secondary retracement range zones time pullback entries

## Discovery Summary

C050-secondary-trend-retracement-range defines the typical pullback boundary in an ongoing trend, while EN068-4060-retracement-zones-for-timing-entries operationalizes that concept into a specific entry rule: wait for the pullback to reach the 40–60% retracement zone before entering. This aligns with Murphy's ideal entry point, which occurs when the retracement has tested the secondary correction range rather than on the initial pullback. The rule thus confirms the risk guideline that entries should be timed within the retracement zone, not on breakout continuation alone.

## Trading Implication

In an uptrend, do not buy the first dip; instead, set limit orders around the 40–60% Fibonacci retracement of the prior impulse leg, with a stop below the retracement low.

## Supporting Notes

- [[C050-secondary-trend-retracement-range]]
- [[EN068-4060-retracement-zones-for-timing-entries]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
