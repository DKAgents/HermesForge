---
type: insight
date: 2026-09-13
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
---

# Filter Oversold Entries with Breadth Oscillator

## Discovery Summary

The oscillator entry strategy (EN041) exploits secondary trends (C366) by buying oversold pullbacks in an uptrend. However, in strong trends oscillators can give premature or false oversold signals when only a few large-cap stocks correct while broad market breadth remains buoyant. Using the McClellan Oscillator (N186), which measures advancing vs. declining issues, as a filter ensures the pullback is a genuine broad secondary decline—entering only when breadth also reflects a meaningful oversold condition or downturn.

## Trading Implication

Before taking an oversold buy signal in an uptrend based on a momentum oscillator, confirm that the McClellan Oscillator has dropped below zero or is showing a declining trend, rejecting entries when breadth remains strong despite the oscillator reading.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**creates_filter** — Actionability score: 4/5
