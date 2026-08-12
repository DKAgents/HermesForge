---
type: insight
date: 2026-08-05
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
# Breadth Oscillator Filters False Oversold Signals in Primary Trends

## Discovery Summary

EN041 instructs traders to buy oversold conditions in uptrends, but warns implicitly that oscillators can lie in strong trends by staying oversold longer than expected. C366 defines secondary trends as counter-primary corrections lasting weeks to months — precisely the periods when oscillators flash oversold. N186's McClellan Oscillator measures broad market breadth rather than a single instrument, meaning it is less susceptible to individual-stock trend distortion. Using McClellan as a confirming filter — only acting on individual-instrument oversold signals when McClellan also shows broad-market oversold conditions — adds a breadth confirmation layer that distinguishes genuine secondary-trend pullbacks (broad selling) from single-stock idiosyncratic weakness (where the oscillator may remain depressed for structural reasons).

## Trading Implication

In an uptrend, only act on oversold oscillator buy signals from individual instruments when the McClellan Oscillator simultaneously confirms broad-market oversold conditions, filtering out false counter-trend entries where oscillators may stay suppressed due to trend strength in individual issues.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
