---
type: insight
date: 2026-07-30
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
---

# McClellan Oscillator Filters Counter-Trend Entries During Secondary Corrections

## Discovery Summary

EN041 establishes that oscillators should be used with-trend (buy oversold in uptrend, sell overbought in downtrend), but oscillators frequently lie during strong trends by staying overbought/oversold for extended periods. C366 defines secondary trends as counter-primary corrections lasting weeks to months — precisely the periods when oscillators appear 'oversold' in an uptrend. N186's McClellan Oscillator provides a breadth-based confirmation layer: because it measures advancing vs. declining issues across the broad market, it can distinguish between genuine market-wide oversold conditions (secondary trend correction bottoming) versus a single oscillator lying in a persistent strong trend, reducing false counter-trend signals.

## Trading Implication

When a momentum oscillator signals oversold during an uptrend's secondary correction, require the McClellan Oscillator to also show broad-market oversold confirmation before entering; a divergence where price oscillators show oversold but McClellan remains neutral suggests trend strength is lying to the oscillator, warranting no entry.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5
