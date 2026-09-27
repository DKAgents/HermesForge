---
type: insight
date: 2026-08-09
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
# McClellan Breadth Confirms Secondary Trend vs Oscillator Noise

## Discovery Summary

EN041 correctly states to use oscillators with the primary trend, but oscillators 'lie' in strong trends by staying overbought/oversold for extended periods — this is the edge condition. Secondary trends (C366) are precisely the intermediate counter-moves where oscillators temporarily normalize, creating false entry signals. The McClellan Oscillator (N186) measures broad market breadth, not individual security momentum, which means it can distinguish whether a pullback to oversold conditions reflects genuine secondary trend exhaustion across the market versus a brief oscillator reset within an ongoing primary trend impulse.

## Trading Implication

Before acting on EN041's oversold-in-uptrend buy signal, confirm with the McClellan Oscillator that broad market breadth is also pulling back — if the McClellan is still overbought while a single oscillator reads oversold, the signal is likely false and the primary trend is dominating; only enter when both align.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
