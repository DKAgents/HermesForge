---
type: insight
date: 2026-09-04
actionability: 4
connection_type: creates_filter
domains: [risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
---

# Stop placement conflict: technical level vs pivot rule

## Discovery Summary

RG035 mandates stops at valid technical levels (below support for longs), while EN071's pivot point rules place protective stops below the current day's low or today's open, which may not coincide with any established support. This creates a direct conflict when a pivot-based stop is above a key support level, exposing the trade to premature exit while a technically valid stop below support would likely violate the 3:1 reward/risk requirement due to greater distance. Traders must filter pivot signals by checking whether the rule's prescribed stop level satisfies both technical validity and the 3:1 ratio.

## Trading Implication

Before taking a pivot point buy signal from EN071, verify the protective stop placement aligns with a valid support level from RG035; if the pivot-based stop sits above support, either widen the stop to below support and recalculate position size per the money management rule, or skip the trade if the adjusted risk violates the 3:1 reward/risk threshold.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**creates_filter** — Actionability score: 4/5
