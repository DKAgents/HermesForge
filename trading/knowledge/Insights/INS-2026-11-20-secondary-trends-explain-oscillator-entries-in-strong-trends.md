---
type: insight
date: 2026-11-20
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Secondary trends explain oscillator entries in strong trends

## Discovery Summary

EN041's rule to buy oversold in an uptrend and sell short overbought in a downtrend implicitly depends on secondary trends (C366), because oversold/overbought extremes usually occur during counter-trend corrections or rallies within the primary trend. In a strong primary trend, oscillators such as the McClellan Oscillator (N186) can remain overbought/oversold for extended periods, so the extreme signal alone is not a reliable standalone trigger. The missing condition is that the signal must occur in a secondary trend context, which reconciles the oscillator rule with risk rules that ban outright counter-trend trading.

## Trading Implication

Do not trade oscillator extremes as raw signals in strong trends; first confirm that price is in a secondary pullback/rally against the primary trend and take the entry in the direction of the primary trend only.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[INS-2026-11-18-filter-oscillator-entries-with-secondary-trend-context|Filter Oscillator Entries with Secondary Trend Context]]
