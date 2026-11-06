---
type: insight
date: 2026-11-01
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
# Violated support and gaps set stops and position size

## Discovery Summary

C065 (Murphy, p. 83) shows that a broken support level becomes resistance in a downtrend; EN069 shows that price gaps provide concrete support/resistance zones with entry triggers and protective stops beyond the zone. Together they confirm the risk rule that every trade's stop distance should be set by the nearest structural S/R level, not by an arbitrary percentage. That stop distance then drives position size, allowing the same Murphy-based S/R logic to work for long entries off gap support and short entries off prior support as resistance.

## Trading Implication

Before each entry, mark the nearest S/R level from these rules—old support above a bear-market rally, or a gap edge in a pullback—and place the stop beyond it. Compute position size from that stop distance to keep per-trade risk constant; a cluster of gap and prior S/R makes the level more meaningful.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[C336-support-level|Support Level]]
