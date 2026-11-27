---
type: insight
date: 2026-11-26
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
# Secondary trends filter oscillator entries in strong trends

## Discovery Summary

The secondary trends concept (C366) defines counter-trend moves lasting 3 weeks to months, which are the typical pullbacks that create oversold conditions in an uptrend. The oscillator entry rule (EN041) instructs buying oversold conditions in uptrends, but in strong trends, oscillators like the McClellan (N186) can remain overbought/oversold for extended periods, making naive oscillator signals unreliable. Therefore, oscillator entries should be constrained to occur during a confirmed secondary trend, and the McClellan can help identify when breadth extremes signal an overextended move rather than a tradable pullback.

## Trading Implication

Only take buy signals when the pullback resembles a secondary trend (duration 3 weeks+) within a primary uptrend, and confirm that the McClellan Oscillator is not at an extreme that suggests the correction is insufficient; this filters out false entries in strong trends.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**creates_filter** — Actionability score: 4/5
