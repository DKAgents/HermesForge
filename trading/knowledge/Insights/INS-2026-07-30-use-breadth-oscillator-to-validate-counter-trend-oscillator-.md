---
type: insight
date: 2026-07-30
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Use Breadth Oscillator to Validate Counter-Trend Oscillator Signals

## Discovery Summary

EN041 states to buy oversold conditions in uptrends and sell overbought in downtrends, but oscillators notoriously give false readings in strong trends. C366 identifies secondary trends as counter-primary corrections lasting weeks to months — exactly the timeframe where individual oscillators lie most. N186's McClellan Oscillator measures broad market breadth, not a single security, making it more resistant to single-stock trend distortion. A secondary-trend correction confirmed by McClellan Oscillator oversold readings provides a higher-confidence entry signal than a security-level oscillator alone.

## Trading Implication

Only act on oscillator oversold buy signals during a primary uptrend when the McClellan Oscillator also shows broad market oversold conditions, confirming the secondary correction is a breadth-driven pullback rather than an isolated breakdown. Avoid counter-trend trades where the McClellan Oscillator remains neutral or overbought, as this suggests the individual security oscillator signal is noise within a still-strong trend.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related
- [[R268-technical-analysis-checklist-market-analysis-phase]] — Validate oscillator signals with breadth oscillator

- [[R145-combining-contrary-opinion-with-technical-tools]] — See R145-combining-contrary-opinion-with-technical-tools for timing oscillator signals with sentiment extremes

- [[EN086-counter-trend-oscillator-based-trading]] — Validate with breadth oscillator
