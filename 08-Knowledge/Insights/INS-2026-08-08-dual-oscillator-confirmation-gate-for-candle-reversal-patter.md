---
type: insight
date: 2026-08-08
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
# Dual Oscillator Confirmation Gate for Candle Reversal Patterns

## Discovery Summary

C149 establishes that RSI and Stochastics reaching extremes simultaneously produces the strongest signals. R177 states that any oscillator in its overbought/oversold zone can filter candle reversal patterns. N165 defines RSI extremes as above 70 or below 30. Combining these: requiring BOTH RSI (above 70/below 30 per N165) AND Stochastics to be simultaneously in extreme territory (per C149) before validating a candle reversal pattern (per R177) creates a higher-confidence dual-oscillator gate that neither note individually specifies.

## Trading Implication

Only act on candle reversal patterns when both RSI (>70 overbought or <30 oversold) AND Stochastics are simultaneously in their extreme zones — skip candle signals confirmed by only one oscillator, as dual confirmation per C149 produces the best signals.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
