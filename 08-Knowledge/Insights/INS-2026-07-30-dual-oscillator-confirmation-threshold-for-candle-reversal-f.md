---
type: insight
date: 2026-07-30
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Dual Oscillator Confirmation Threshold for Candle Reversal Filters

## Discovery Summary

R177-filtered-candle-patterns-oscillator-alternatives establishes that any oscillator can filter candle reversals, requiring the oscillator to be in its presignal extreme zone before the pattern is valid. C149-rsi-vs-stochastics-volatility-comparison reveals that RSI reaches extremes less frequently than stochastics, but both simultaneously in extreme territory produces the best signals. Combining these: when BOTH RSI (N165, using the 70/30 thresholds) AND stochastics are simultaneously overbought or oversold, a candle reversal pattern appearing at that moment carries a compounded confirmation — satisfying R177's oscillator filter with the highest-confidence oscillator reading described in C149. This dual-oscillator filter is stricter than using either oscillator alone, reducing false candle pattern signals.

## Trading Implication

Only act on candle reversal patterns when BOTH RSI (above 70 or below 30) AND stochastics are simultaneously in overbought or oversold territory; treat single-oscillator extreme readings as insufficient confirmation and wait for dual confirmation before entering.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related
- [[N062-macd-divergence-analysis]] — See MACD divergence as potential third oscillator confirmation

- [[N082-filtered-candle-patterns-stochastics-d-application]] — See N082-filtered-candle-patterns-stochastics-d-application for the Stochastics %D presignal threshold that defines the overbought/oversold extreme zone
