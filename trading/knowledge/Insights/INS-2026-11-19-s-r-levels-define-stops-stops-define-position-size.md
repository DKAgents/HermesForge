---
type: insight
date: 2026-11-19
actionability: 4
connection_type: confirms_risk_rule
domains: [entry timing, position sizing, risk management, support/resistance, trend trading]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "EN069-price-gaps-as-support-and-resistance-for-timing"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# S/R Levels Define Stops, Stops Define Position Size

## Discovery Summary

C065 (previous support as future resistance, Murphy p.83) and EN069 (gaps as support/resistance) provide objective levels for stop placement. The seed risk guideline links these levels to position sizing: stop distance from entry defines per-share risk, which sets position size. Together, Murphy's S/R rules create a two-sided framework — long dips into gap support in uptrends, short rallies into former support/gap resistance in downtrends — with stops and size determined by the same levels.

## Trading Implication

Before entering, identify the relevant gap edge or flipped prior support level, place the protective stop just beyond it, and size the position so that a stop-out equals your predefined dollar risk. Apply this on both long and short setups where Murphy-defined S/R levels are present.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[C336-support-level|Support Level]]
