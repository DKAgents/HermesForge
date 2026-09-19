---
type: insight
date: 2026-09-18
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "EN069-price-gaps-as-support-and-resistance-for-timing", "RG035-combining-technical-factors-with-money-management-for-stop-p"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Support/Resistance Levels Drive Position Sizing via Stops

## Discovery Summary

Note C065 explains that violated support becomes resistance in downtrends, while EN069 describes how price gaps act as support/resistance. RG035 mandates that protective stops must be placed at valid technical levels (below support for longs, above resistance for shorts) and that the stop distance directly determines position size via money management rules. Together, they form a concrete workflow: identify a support/resistance level (e.g., a violated prior support or a gap), set the stop just beyond it, then compute the maximum position size based on the account's risk per trade.

## Trading Implication

Traders should systematically map support/resistance levels from C065 and EN069, then use RG035's stop-placement criteria to derive the exact stop distance, which in turn dictates the maximum position size allowed under their risk management rules.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
