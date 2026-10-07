---
type: insight
date: 2026-10-03
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk management, rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "R312-reversal-of-roles-supportresistance"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Support/resistance role reversal sets stop distance and position size

## Discovery Summary

C065 (previous-support-as-future-resistance-in-downtrend) and R312 (reversal-of-roles-supportresistance) both define the same principle: prior support becomes resistance in a downtrend. This directly informs stop placement because the flipped level acts as a natural invalidation point; placing stops beyond it (or using it as a profit target) aligns with the rule. The seed question extends this to position sizing: tighter stops near the flipped level allow larger size, wider stops require smaller size, so the notes confirm a risk-rule linkage.

## Trading Implication

In a downtrend, identify the last major support zone above price; after it breaks, use it as a resistance level to place stops just above it, and calculate position size based on that stop distance to maintain consistent risk.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[R312-reversal-of-roles-supportresistance]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[C334-resistance-level|Resistance Level]]
