---
type: insight
date: 2026-09-10
actionability: 3
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
# McClellan Oscillator Validates Secondary Trend Countermoves in Strong Markets

## Discovery Summary

EN041's oscillator entry strategy advises fading overbought/oversold conditions in alignment with the primary trend, but provides no distinction between primary and secondary trend phases. C366 defines secondary trends as counter-primary moves lasting weeks to months, creating a window where fading the oscillator could trap a trader in an accelerating correction. The McClellan Oscillator (N186) can serve as a breadth-confirmation filter: when it diverges from price during an overbought/oversold signal, it warns the secondary trend may extend further, delaying entry until the oscillator cross (the alternative rule in EN041) confirms resumption of the primary trend.

## Trading Implication

Before fading an overbought/oversold signal in a trending market per EN041, check the McClellan Oscillator for breadth divergence. If divergence is present, wait for a zero-line cross on the momentum oscillator before entering, avoiding premature trades that get run over by a secondary trend.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 3/5
