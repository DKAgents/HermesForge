---
type: insight
date: 2026-09-24
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# RSI as Candle Pattern Filter Using Overbought/Oversold

## Discovery Summary

Combining C149 (RSI vs Stochastics) and R177 (Filtered Candle Patterns) with N165 (RSI levels) reveals that RSI's lower volatility and less frequent extremes make it a stronger filter for candle reversal patterns. R177 states any oscillator can filter, but C149 notes RSI reaches extremes less often, meaning trades triggered only when RSI is simultaneously in overbought/oversold territory (70/30) have higher confirmation. The best signals occur when both RSI and Stochastics are in extreme zones simultaneously, per C149.

## Trading Implication

When a candle reversal pattern appears, only enter the trade if RSI is in overbought (>70 for bearish) or oversold (<30 for bullish) territory. For even stronger confirmation, also require Stochastics to be in its extreme zone at the same time.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**adds_condition** — Actionability score: 4/5
