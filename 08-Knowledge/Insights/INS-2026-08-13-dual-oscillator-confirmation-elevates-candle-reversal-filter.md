---
type: insight
date: 2026-08-13
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C149-rsi-vs-stochastics-volatility-comparison", "N165-relative-strength-index-rsi-overboughtoversold-levels", "R177-filtered-candle-patterns-oscillator-alternatives"]
seed_id: reversal_pattern_oscillator
tags: [insight, discovery, knowledge-evolution]
---

# Dual Oscillator Confirmation Elevates Candle Reversal Filter Quality

## Discovery Summary

R177-filtered-candle-patterns-oscillator-alternatives establishes that any oscillator in its presignal (overbought/oversold) area can validate a candle reversal pattern. C149-rsi-vs-stochastics-volatility-comparison adds the non-obvious insight that RSI reaches extremes less frequently than Stochastics, meaning when RSI is simultaneously in overbought/oversold territory alongside Stochastics, the signal is rarer and arguably higher-conviction. N165-relative-strength-index-rsi-overboughtoversold-levels provides the specific RSI thresholds (above 70 / below 30) plus the divergence criterion. Combined, requiring BOTH RSI and Stochastics to be in their extreme zones before accepting a candle reversal pattern creates a dual-oscillator filter that is stricter and more selective than using either alone.

## Trading Implication

Only act on candle reversal patterns when BOTH RSI (>70 overbought or <30 oversold) AND Stochastics are simultaneously in their respective extreme zones; skip setups where only one oscillator confirms, as the dual-confirmation raises signal quality by exploiting RSI's lower frequency of reaching extremes.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**adds_condition** — Actionability score: 4/5
