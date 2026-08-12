---
type: insight
date: 2026-08-07
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
# Breadth Oscillator Filters Counter-Trend Entries During Secondary Corrections

## Discovery Summary

EN041 establishes that oscillators should only generate counter-trend signals when aligned with the primary trend (buy oversold in uptrends, sell overbought in downtrends). C366 defines secondary trends as counter-primary corrections lasting weeks to months — exactly the conditions where oscillators most frequently generate misleading 'overbought' readings in strong trends. N186's McClellan Oscillator operates on market breadth rather than price, which means it can distinguish whether a price pullback is accompanied by genuine broad market deterioration (true secondary trend) versus a narrow-issue correction where breadth remains healthy — filtering out the 'oscillator lies in strong trends' problem by adding a breadth confirmation requirement before acting on overbought/oversold signals.

## Trading Implication

Before acting on an oscillator overbought/oversold signal during an established primary trend, confirm the reading with McClellan Oscillator breadth data — only take counter-trend entries when breadth confirms the secondary correction, avoiding false signals where price oscillators are merely 'lying' due to trend momentum.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
