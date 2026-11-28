---
type: insight
date: 2026-11-27
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Trade secondary corrections with primary-trend oscillator signals

## Discovery Summary

C366-secondary-trends defines intermediate counter-trend moves within a primary trend. EN041-oscillator-entry-strategy-in-trending-markets already says to buy oversold conditions only in uptrends and sell overbought only in downtrends. The McClellan Oscillator (N186) can serve as the breadth-based oscillator for this rule. In strong trends oscillators can stay overbought/oversold, so the non-obvious connection is to treat these readings as signals of a secondary move, not a reversal, and enter only in the direction of the primary trend once the secondary correction appears exhausted.

## Trading Implication

In a primary uptrend, wait for a secondary decline to push the McClellan Oscillator oversold, then buy; ignore overbought breadth as a short signal. In a primary downtrend, do the reverse: sell overbought secondary rallies, ignore oversold breadth as a buy signal.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**creates_filter** — Actionability score: 4/5
