---
type: insight
date: 2026-11-10
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, trading_rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# RSI-Stochastic Confluence Filter for Candle Reversal Patterns

## Discovery Summary

R177 says any oscillator can filter candle reversal patterns if it is in its presignal overbought/oversold zone. C149 adds that RSI is less volatile and reaches extremes less often than Stochastics, and that the best signals occur when both oscillators are simultaneously overbought or oversold. N165 supplies concrete RSI extremes of above 70 or below 30. Together, these notes create a stricter confluence filter: require both RSI and Stochastics to be in extreme territory before accepting a candle reversal signal.

## Trading Implication

Do not act on a candle reversal pattern unless RSI is beyond 70/30 and Stochastics is simultaneously overbought/oversold; this filters out weaker reversal signals and improves confirmation quality.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
