---
type: insight
date: 2026-08-05
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

R177-filtered-candle-patterns-oscillator-alternatives establishes that any oscillator in overbought/oversold territory can validate a candle reversal pattern. C149-rsi-vs-stochastics-volatility-comparison reveals that RSI reaches extremes less frequently than Stochastics, meaning RSI confirmation is a stricter, higher-conviction gate. Combining both — requiring simultaneous RSI and Stochastics extremes per C149 before accepting a candle reversal signal per R177 — creates a two-layer filter that eliminates lower-quality setups while dramatically increasing signal reliability. N165-relative-strength-index-rsi-overboughtoversold-levels anchors the RSI threshold rules (above 70 overbought, below 30 oversold) needed to operationalize this dual-gate.

## Trading Implication

Only act on a candle reversal pattern when BOTH RSI (above 70 or below 30) AND Stochastics %D are simultaneously in their respective overbought or oversold zones; treat single-oscillator confirmation as insufficient and wait for the dual extreme condition before entering.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5
