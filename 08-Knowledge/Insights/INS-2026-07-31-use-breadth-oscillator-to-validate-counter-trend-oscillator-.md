---
type: insight
date: 2026-07-31
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

EN041 prescribes buying oversold conditions within an uptrend, but oscillators notoriously give false oversold readings during strong trending phases. C366 defines secondary trends as counter-primary corrections lasting weeks to months — precisely the context where oversold readings appear on momentum oscillators. N186's McClellan Oscillator provides a breadth-based confirmation layer: if individual stock oscillators flash oversold but the McClellan Oscillator (measuring broad market advancing/declining issues) is NOT confirming oversold conditions at the market level, the individual oversold signal is likely a false read produced by trend strength rather than a genuine secondary-trend correction bottom.

## Trading Implication

Before acting on an oversold oscillator entry signal in an uptrend (per EN041), require the McClellan Oscillator to also show a corresponding oversold reading — if McClellan remains neutral or overbought while price oscillators show oversold, treat it as a trend-strength artifact and stand aside rather than buying the counter-trend dip.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related
- [[R145-combining-contrary-opinion-with-technical-tools]] — See R145-combining-contrary-opinion-with-technical-tools for another confirmation filter using sentiment extremes

- [[R268-technical-analysis-checklist-market-analysis-phase]] — See Note A for breadth confirmation of oscillator signals

- [[EN086-counter-trend-oscillator-based-trading]] — Validate with breadth oscillator
