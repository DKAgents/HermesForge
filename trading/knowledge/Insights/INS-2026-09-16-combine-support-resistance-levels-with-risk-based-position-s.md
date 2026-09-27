---
type: insight
date: 2026-09-16
actionability: 4
connection_type: reveals_sequence
domains: [concepts, risk-guidelines, rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "EN069-price-gaps-as-support-and-resistance-for-timing", "RG035-combining-technical-factors-with-money-management-for-stop-p"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Combine support/resistance levels with risk-based position sizing

## Discovery Summary

C065 and EN069 provide specific technical levels (violated support as resistance, gaps as support/resistance) for stop placement. RG035 then mandates that stops must be placed at valid technical levels and uses the stop distance to calculate position size based on a fixed risk percentage. Together, they form a step-by-step procedure: identify a valid support/resistance level from C065 or EN069, set the stop just beyond it, then compute position size using the risk per trade rule from RG035.

## Trading Implication

Before entering a trade, identify a precise stop level using prior support/resistance or gap levels, then determine position size such that the total risk (stop distance × position size) does not exceed the maximum allowed risk per trade (e.g., 5% of account).

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5

## Related Notes
- [[C334-resistance-level|Resistance Level]]
