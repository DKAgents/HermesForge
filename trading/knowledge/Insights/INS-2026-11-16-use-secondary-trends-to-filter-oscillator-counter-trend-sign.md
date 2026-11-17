---
type: insight
date: 2026-11-16
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, trading rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Use secondary trends to filter oscillator counter-trend signals

## Discovery Summary

EN041-oscillator-entry-strategy-in-trending-markets says to buy oversold in uptrends, but strong trends can keep oscillators overbought/oversold and generate premature signals. C366-secondary-trends adds the missing filter: wait for a secondary correction/rally—one lasting roughly three weeks to months—before acting on an oscillator extreme in the direction of the primary trend. N186-mcclellan-oscillator provides a breadth-based oscillator that can identify these broad-market extremes, but its readings should be interpreted only in the context of that secondary trend. This respects counter-trend risk rules by making the trade counter-secondary but aligned with, not against, the primary trend.

## Trading Implication

In an uptrend, do not sell an overbought oscillator; wait for a secondary decline and buy oversold breadth. In a downtrend, wait for a secondary rally and sell short overbought breadth, avoiding any oscillator signal that triggers against the primary trend.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**creates_filter** — Actionability score: 4/5
