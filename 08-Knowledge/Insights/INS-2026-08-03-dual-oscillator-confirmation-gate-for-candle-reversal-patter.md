---
type: insight
date: 2026-08-03
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

C149 establishes that RSI and Stochastics confirm each other most powerfully when simultaneously in overbought/oversold territory. R177 states that any oscillator can filter candle patterns, requiring the oscillator to be in its presignal zone before a candle reversal is valid. N165 defines RSI's specific thresholds (above 70 / below 30). Combining these: a candle reversal pattern gains its strongest confirmation not from a single oscillator filter but from requiring BOTH RSI (above 70 or below 30) AND Stochastics to be simultaneously in their extreme zones, creating a dual-gate filter.

## Trading Implication

A trader should only act on candle reversal patterns when both RSI (above 70/below 30 per N165) and Stochastics are simultaneously in overbought or oversold territory, treating single-oscillator confirmation as insufficient and waiting for the dual-confirmation condition before entering a position.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
