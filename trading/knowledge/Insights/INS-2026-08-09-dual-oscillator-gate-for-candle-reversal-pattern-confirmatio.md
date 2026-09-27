---
type: insight
date: 2026-08-09
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
# Dual Oscillator Gate for Candle Reversal Pattern Confirmation

## Discovery Summary

C149 establishes that RSI and Stochastics reach extremes at different frequencies, with RSI being less volatile. R177 states that ANY oscillator can filter candle patterns, but requires the oscillator to be in its overbought/oversold zone BEFORE the candle reversal pattern appears. N165 defines RSI's overbought/oversold thresholds at 70/30. The non-obvious connection is that requiring BOTH RSI (above 70 or below 30) AND Stochastics to simultaneously be in extreme territory — as suggested by C149 — creates a dual-oscillator filter for candle reversal patterns per R177, producing a higher-conviction confirmation signal than either oscillator alone, since RSI's relative rarity of extremes acts as a stricter pre-qualifier.

## Trading Implication

Before acting on a candle reversal pattern, require both RSI (>70 or <30) and Stochastics to simultaneously show overbought or oversold readings; treat RSI crossing the 70/30 threshold as the primary qualifying gate since it triggers less frequently, then use Stochastics agreement as the confirmation layer.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
