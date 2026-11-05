---
type: insight
date: 2026-11-04
actionability: 5
connection_type: creates_filter
domains: [concepts, indicators, patterns, trading_rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# RSI-Stochastic Double Filter Confirms Candle Reversals

## Discovery Summary

R177 states that any oscillator, including Wilder's RSI, can filter candle patterns, but the oscillator must be in its presignal overbought/oversold area before a candle reversal pattern is valid. N165 defines that area as RSI above 70 or below 30 and notes divergence from price warns of a trend reversal. C149 adds that RSI is less volatile and reaches extremes less often than stochastics, so requiring RSI extreme readings is a strict filter, and the best confirmation occurs when RSI and stochastics are simultaneously in the same extreme zone.

## Trading Implication

Before acting on a bullish reversal candle, require RSI below 30; for a bearish reversal candle, require RSI above 70. For stronger confirmation, also require stochastics to be in the same overbought/oversold zone before entering the trade.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 5/5
