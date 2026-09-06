---
type: insight
date: 2026-09-06
actionability: 4
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# Dual-Oscillator Filter for Candle Patterns

## Discovery Summary

C149 notes that RSI is less volatile and reaches extremes less frequently, and the best signals come when both RSI and stochastics are simultaneously overbought/oversold. R177 states that any oscillator can filter candle patterns, requiring the oscillator to be in its presignal area. Combining these, a high-confidence filter emerges: only consider a candle reversal pattern valid when both RSI and stochastics confirm with overbought/oversold readings, leveraging RSI's lower noise and dual confirmation to reduce false signals.

## Trading Implication

Before acting on a candle reversal pattern, require both RSI and stochastics to be in their respective overbought or oversold zones simultaneously; this filters out weaker signals and improves entry timing.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
