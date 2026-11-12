---
type: insight
date: 2026-11-11
actionability: 4
connection_type: adds_condition
domains: [candlestick_patterns, indicators, trading_rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# RSI and Stochastic Confluence Filters Candle Reversals

## Discovery Summary

R177 states that any oscillator can filter candle reversal patterns, but only when it is in its overbought/oversold presignal area. C149 adds that the best signals occur when RSI and stochastics are simultaneously overbought or oversold, and N165 defines RSI extremes as above 70 or below 30 with divergence warning of reversal. Therefore, a candle reversal pattern becomes more reliable when both RSI and stochastics confirm the same extreme condition, with RSI's less frequent extremes filtering out marginal signals.

## Trading Implication

Do not act on a candle reversal pattern unless RSI is above 70 (bearish) or below 30 (bullish) AND stochastics is simultaneously in its overbought/oversold zone. Treat RSI divergence as an additional confirmation warning.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**adds_condition** — Actionability score: 4/5
