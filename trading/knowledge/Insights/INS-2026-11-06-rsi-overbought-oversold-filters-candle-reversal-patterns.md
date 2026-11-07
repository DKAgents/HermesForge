---
type: insight
date: 2026-11-06
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, patterns, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# RSI Overbought/Oversold Filters Candle Reversal Patterns

## Discovery Summary

R177 'Filtered Candle Patterns — Oscillator Alternatives' explicitly allows any oscillator to filter candle patterns, including Wilder's RSI. N165 defines RSI overbought/oversold at 70/30 and notes divergence warns of reversals. C149 adds that RSI is less volatile than stochastics and best when both oscillators agree. Thus, combining a candle reversal pattern with RSI in the extreme zone (above 70 or below 30) provides a stronger confirmation than using the pattern alone, especially when divergence is present.

## Trading Implication

Before acting on any bullish or bearish candle reversal pattern, require RSI to be in oversold (<30) or overbought (>70) territory respectively, and ideally check for RSI divergence to increase signal reliability.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
