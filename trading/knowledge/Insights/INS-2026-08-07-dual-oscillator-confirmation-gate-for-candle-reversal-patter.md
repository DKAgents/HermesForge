---
type: insight
date: 2026-08-07
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

C149 establishes that the strongest signals occur when both RSI and Stochastics simultaneously reach overbought/oversold extremes. R177 states that any oscillator — explicitly including RSI — can filter candle patterns, requiring the oscillator to be in its presignal zone before a reversal candle is considered valid. Combining these: since RSI reaches extremes less frequently than Stochastics (C149), requiring BOTH to be simultaneously in extreme territory (as Murphy recommends) creates a high-specificity dual-confirmation gate for candle reversal patterns, dramatically reducing false signals beyond what either oscillator alone provides. N165 anchors the RSI threshold levels precisely at 70/30, giving the filter concrete numeric boundaries.

## Trading Implication

A trader should only act on candle reversal patterns (e.g., engulfing, hammer, doji) when BOTH RSI is above 70 or below 30 AND Stochastics %D is simultaneously in overbought/oversold territory — treating the dual-oscillator alignment as a mandatory pre-condition rather than optional confirmation.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
