---
type: insight
date: 2026-07-26
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
# Breadth Oscillator Confirms Counter-Trend Entry Timing

## Discovery Summary

EN041-oscillator-entry-strategy-in-trending-markets establishes that oscillators should only be faded (bought oversold, sold overbought) in the direction of the primary trend — never against it. C366-secondary-trends defines exactly the phenomenon EN041 is capturing: secondary trends ARE counter-primary corrections. The non-obvious link is that N186-mcclellan-oscillator, a breadth-based oscillator, adds a market-wide confirmation layer EN041 lacks: single-instrument oscillators can remain extreme in strong trends (the classic 'oscillator lie'), but a breadth extreme in the McClellan Oscillator signals broad participation in the secondary-trend correction, making the oversold/overbought condition more structurally reliable and less likely to be a false signal driven by price alone.

## Trading Implication

When trading a primary-trend pullback per EN041, require the McClellan Oscillator to confirm an oversold (uptrend) or overbought (downtrend) breadth reading before entry — this filters out single-stock or sector-driven oscillator extremes that do not reflect a genuine secondary-trend exhaustion across the broad market.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[INS-2026-08-16-use-breadth-oscillator-to-confirm-secondary-trend-entries|Use Breadth Oscillator to Confirm Secondary Trend Entries]]
