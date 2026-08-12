---
type: insight
date: 2026-08-11
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

C149 establishes that RSI and Stochastics reach extremes at different frequencies, and that simultaneous extremes in both provide the strongest signals. R177 states that any oscillator can filter candle patterns, but only requires one oscillator to be in its presignal zone. Combining these two notes yields a stricter, more selective filter: require BOTH RSI (above 70/below 30, per N165) AND Stochastics to be simultaneously overbought/oversold before a candle reversal pattern is considered valid. Since RSI reaches extremes less frequently than Stochastics (C149), this dual-gate condition is a higher-conviction threshold than using either oscillator alone.

## Trading Implication

Only act on candle reversal patterns when both RSI (>70 overbought or <30 oversold) and Stochastics are simultaneously in their respective extreme zones, treating this dual confirmation as a mandatory pre-filter rather than using a single oscillator as R177 minimally requires.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
