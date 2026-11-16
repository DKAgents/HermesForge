---
type: insight
date: 2026-11-15
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, position sizing, price gaps, risk management, trading rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "EN069-price-gaps-as-support-and-resistance-for-timing"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# S/R Levels Define Stops and Position Sizing

## Discovery Summary

C065 states that in a downtrend, violated support flips to resistance, giving a precise short-entry zone. EN069 similarly identifies gaps as support/resistance for entry timing, with stops placed beyond the gap. Both rules imply a clear stop distance, which directly determines position size when a fixed fractional risk model is used. The seed question ties these together: the technical level defines the stop, and the stop defines the size.

## Trading Implication

When entering on a prior-support-now-resistance bounce in a downtrend, or a gap test, always place the protective stop one tick beyond the identified level, then size the position so that the stop-loss distance equals the allowed dollar risk per trade.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
