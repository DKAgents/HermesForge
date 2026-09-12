---
type: insight
date: 2026-09-11
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Dual Oscillator Extreme Filter for Candle Patterns

## Discovery Summary

Rule R177 establishes that any oscillator can filter candle reversal patterns by requiring it to be in overbought or oversold territory before a pattern is valid. Concept C149 notes that RSI is less volatile than stochastics and that the best signals occur when both RSI and stochastics are simultaneously in overbought or oversold territory. Combining these insights yields a specific filter: validate a candle reversal pattern only when both RSI (from N165, using 70/30 levels) and stochastics confirm extreme readings, thereby filtering out weaker single-oscillator signals.

## Trading Implication

Only trade a candle reversal pattern when both RSI and stochastics are in their respective overbought or oversold zones simultaneously, discarding patterns confirmed by just one oscillator.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
