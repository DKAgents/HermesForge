---
type: insight
date: 2026-09-18
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# RSI-Stochastics Confluence for Candle Pattern Filters

## Discovery Summary

C149 notes that best RSI-Stochastics signals occur when both are simultaneously overbought/oversold. R177 states any oscillator can filter candle patterns. Combining these yields a specific filter: confirm reversal candle patterns only when both RSI (N165's standard levels) and Stochastics are in extreme territory.

## Trading Implication

When a candle reversal pattern appears, only execute the trade if both RSI and Stochastics are concurrently overbought (bearish) or oversold (bullish).

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
