---
type: insight
date: 2026-11-03
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Secondary corrections align oscillator entries with primary trend

## Discovery Summary

C366-secondary-trends defines intermediate counter-trend moves that last weeks to months; these are the pullbacks/rallies that EN041-oscillator-entry-strategy-in-trending-markets exploits by buying oversold conditions in uptrends and selling overbought conditions in downtrends. In strong trends, oscillators lie, so overbought/oversold extremes can be misleading; the zero-line cross variant in EN041 provides a better entry trigger when the primary trend is intact. N186-mcclellan-oscillator can supply the breadth-based oscillator reading to time these secondary-trend entries. This confirms the risk rule that counter-trend trades should be avoided unless they are entries aligned with the larger primary trend.

## Trading Implication

In a strong primary trend, do not short overbought readings or buy oversold readings as reversals; instead wait for a secondary correction and enter with the primary trend, using a zero-line cross as the trigger.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
