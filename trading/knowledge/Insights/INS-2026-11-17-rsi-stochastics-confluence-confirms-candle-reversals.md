---
type: insight
date: 2026-11-17
actionability: 4
connection_type: creates_filter
domains: [candlestick patterns, indicators, oscillators, trading rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# RSI + Stochastics Confluence Confirms Candle Reversals

## Discovery Summary

R177 states that any oscillator can filter candle patterns, provided the oscillator is in its presignal overbought/oversold area before the reversal pattern is valid. C149 adds that RSI is less volatile and reaches extremes less often than stochastics, and that the strongest signals occur when both RSI and stochastics are simultaneously overbought or oversold. N165 defines the RSI extremes as above 70 and below 30, with divergences warning of potential reversals. Together these notes create a high-conviction filter: a candle reversal pattern should only be acted on when RSI and stochastics are aligned in the same overbought/oversold zone.

## Trading Implication

Traders should require both RSI and stochastics to be in overbought territory for bearish candle reversals, or oversold territory for bullish candle reversals, before treating the pattern as a valid signal. This reduces false reversal signals by combining a less volatile oscillator with a confirming one.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
