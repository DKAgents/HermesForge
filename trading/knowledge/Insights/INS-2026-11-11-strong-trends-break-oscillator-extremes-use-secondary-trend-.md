---
type: insight
date: 2026-11-11
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, risk_guidelines, trading_rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Strong Trends Break Oscillator Extremes; Use Secondary Trend Filter

## Discovery Summary

EN041's buy-oversold-in-an-uptrend rule assumes the oversold dip is a secondary pullback rather than a primary reversal, but in strong trends oscillators can remain overbought/oversold and flash misleading extremes. C366 identifies secondary trends as counter-primary moves lasting weeks to months, so the trader must verify that an oversold reading in an uptrend is actually a secondary correction before entering. The McClellan Oscillator's breadth extremes are useful for this, but EN041's zero-line-cross variant is the safer trigger when strong trends make the extreme readings unreliable. This aligns with the risk guideline against counter-trend trades by keeping long entries in the direction of the primary trend.

## Trading Implication

In strong primary trends, do not buy every oversold or sell every overbought reading; wait for zero-line cross confirmation and a secondary-trend pullback/rally against the primary trend before entering. If no extreme occurs because the trend is too strong, use the zero-line-cross entry instead of fading the move.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**creates_filter** — Actionability score: 4/5
