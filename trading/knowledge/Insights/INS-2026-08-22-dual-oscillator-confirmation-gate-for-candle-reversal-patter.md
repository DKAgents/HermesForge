---
type: insight
date: 2026-08-22
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

C149 establishes that RSI reaches extremes less frequently than Stochastics, and that the strongest signals occur when BOTH oscillators are simultaneously in overbought/oversold territory. R177 states that any oscillator can filter candle patterns, requiring the oscillator to be in its presignal area before a reversal pattern is considered valid. Combining these: using BOTH RSI (>70/<30 per N165) AND Stochastics simultaneously in extreme territory as the filter condition for candle reversal patterns creates a higher-conviction gate than using either oscillator alone — since RSI reaches extremes less often, its presence alongside Stochastics extreme readings is a rarer, more meaningful confluence.

## Trading Implication

Only act on candle reversal patterns when BOTH RSI (above 70 or below 30) AND Stochastics are simultaneously in overbought or oversold territory — this dual-oscillator gate reduces false signals by leveraging RSI's lower sensitivity as a confirming filter rather than treating each oscillator independently.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
