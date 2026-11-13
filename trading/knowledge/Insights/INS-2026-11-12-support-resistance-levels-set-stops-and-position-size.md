---
type: insight
date: 2026-11-12
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk guidelines, trading rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "EN069-price-gaps-as-support-and-resistance-for-timing"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Support/Resistance Levels Set Stops and Position Size

## Discovery Summary

C065 (Murphy p.83) shows that in a downtrend, prior support becomes resistance, while EN069 shows that price gaps act as support/resistance and dictate stop placement beyond the gap. Both notes identify objective S/R levels that determine where a protective stop should sit. Since the distance from entry to stop determines risk per unit, these levels feed directly into position sizing. The two Murphy rules therefore confirm the risk rule: use technical S/R to set the stop, then size the position from that stop distance.

## Trading Implication

In a downtrend, short into prior support-turned-resistance with a stop above that level; in an uptrend, buy gap dips with a stop below the gap. In both cases, divide the risk budget by the stop distance to calculate position size.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
