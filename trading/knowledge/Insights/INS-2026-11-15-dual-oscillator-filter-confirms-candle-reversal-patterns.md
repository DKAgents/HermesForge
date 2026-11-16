---
type: insight
date: 2026-11-15
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, trading_rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Dual Oscillator Filter Confirms Candle Reversal Patterns

## Discovery Summary

R177 says any oscillator can filter candle reversal patterns, provided it is in its presignal overbought/oversold area. C149 adds that RSI is less volatile than stochastics and reaches extremes less frequently, and that best signals occur when both oscillators are simultaneously overbought or oversold. N165 defines RSI extremes as above 70 or below 30. Therefore, requiring both RSI and stochastics to be in extreme territory before acting on a candle reversal pattern creates a stricter, higher-quality filter.

## Trading Implication

Only take candle reversal signals when RSI is above 70 or below 30 and stochastics are simultaneously overbought or oversold, reducing false signals because RSI extremes are rarer.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[INS-2026-10-12-use-rsi-extremes-over-stochastics-to-confirm-reversals|Use RSI extremes over Stochastics to confirm reversals]]
