---
type: insight
date: 2026-08-08
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
# McClellan Breadth Filter Validates Oscillator Signals Within Primary Trends

## Discovery Summary

EN041 states oscillators should be used to buy oversold conditions in uptrends and sell overbought in downtrends — but oscillators famously 'lie' in strong trends by remaining overbought/oversold for extended periods. C366 defines secondary trends (counter-trend moves of 3 weeks to months) as the exact conditions where these oscillator signals appear. The non-obvious connection is that N186's McClellan Oscillator, being a breadth-based measure rather than a price-based oscillator, can serve as a confirmation filter: if the McClellan Oscillator shows broad market participation consistent with the primary trend, a price oscillator's 'oversold' reading in an uptrend is more likely a genuine secondary trend correction worth buying, rather than the start of a primary trend reversal.

## Trading Implication

Before acting on an oversold oscillator signal during an uptrend (per EN041), confirm the McClellan Oscillator is not itself deeply negative or trending bearishly — breadth deterioration would suggest the 'secondary trend' correction may be deeper than expected, increasing counter-trend trade risk.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[INS-2026-08-06-mcclellan-breadth-filter-validates-oscillator-signals-within|McClellan Breadth Filter Validates Oscillator Signals Within Primary Trend]]
