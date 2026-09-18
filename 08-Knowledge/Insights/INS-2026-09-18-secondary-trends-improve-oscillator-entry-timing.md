---
type: insight
date: 2026-09-18
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
---

# Secondary trends improve oscillator entry timing

## Discovery Summary

C366-secondary-trends defines counter-trend moves within a primary trend. EN041-oscillator-entry-strategy-in-trending-markets advises buying oversold conditions in an uptrend. However, in strong trends oscillators can remain overbought/oversold for extended periods (the seed question's edge condition). N186-mcclellan-oscillator measures breadth oversold/overbought. The non-obvious connection is that using secondary trend identification (C366) to confirm that a correction is actually underway prevents false signals from oscillator extremes in persistent trends. This adds a condition: only act on oscillator oversold signals when a secondary decline is present.

## Trading Implication

In a strong primary uptrend, do not buy simply because the McClellan oscillator is oversold; instead, wait for a secondary correction (a decline lasting weeks to months) to confirm the oversold condition is part of a genuine counter-trend move, then enter long.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
