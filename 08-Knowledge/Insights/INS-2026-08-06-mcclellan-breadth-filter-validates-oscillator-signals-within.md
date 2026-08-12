---
type: insight
date: 2026-08-06
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
# McClellan Breadth Filter Validates Oscillator Signals Within Primary Trend

## Discovery Summary

EN041 establishes that oscillators should only be used counter-trend within the primary trend direction (buy oversold in uptrend, sell overbought in downtrend). The seed problem is that oscillators lie in strong trends, producing premature signals. N186's McClellan Oscillator measures broad market breadth rather than a single security, meaning it can confirm whether an 'oversold' reading in an individual oscillator coincides with genuine broad market exhaustion versus a continuation of trend strength. C366 defines secondary trends (3 weeks to several months) as the counter-primary corrections where EN041's strategy applies — the McClellan Oscillator can distinguish a true secondary-trend correction from a momentary pause within a still-strong primary trend.

## Trading Implication

Before acting on an oversold oscillator signal in an uptrend, confirm the McClellan Oscillator also shows broad market oversold conditions; if breadth remains strong (McClellan elevated or rising), treat the individual oscillator signal as a false counter-trend setup and stand aside.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
