---
type: insight
date: 2026-11-12
actionability: 4
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
# RSI 70/30 filters candle reversals; Stochastics confirms

## Discovery Summary

R177 says a candle reversal pattern is only valid when an oscillator is already in its presignal overbought/oversold area; N165 defines that area for RSI as above 70 and below 30. C149 explains that RSI reaches these extremes less often than stochastics, making RSI extremes more selective, and that the strongest confirmation occurs when RSI and Stochastics are both in overbought/oversold territory. N165 also notes that price divergence at these RSI extremes warns of a possible trend reversal, adding further confirmation.

## Trading Implication

Require RSI above 70 for bearish candle reversal patterns and below 30 for bullish ones before trading; take the highest-conviction signals when Stochastics is also in the same extreme zone, and weight RSI-price divergence as additional reversal evidence.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
