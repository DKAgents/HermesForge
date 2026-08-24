---
type: insight
date: 2026-08-18
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
# Dual Oscillator Confirmation Gate for Candle Reversal Signals

## Discovery Summary

C149 establishes that RSI and Stochastics have different volatility profiles, with the best signals occurring when both are simultaneously in overbought or oversold territory. R177 states that any oscillator — including RSI — can filter candle reversal patterns, requiring the oscillator to be in its presignal area before the pattern is considered valid. Combining these: rather than using a single oscillator as the candle-pattern filter (as R177 implies), requiring BOTH RSI (per N165, above 70 or below 30) AND Stochastics to be simultaneously in extreme territory before accepting a candle reversal creates a higher-confidence, dual-confirmation filter. This is non-obvious because R177 treats oscillator choice as interchangeable, while C149 reveals the cross-oscillator confirmation principle as the superior signal condition.

## Trading Implication

A trader should only act on candle reversal patterns when BOTH RSI (>70 overbought / <30 oversold) and Stochastics are simultaneously in their extreme zones, using the dual-oscillator agreement as the filter rather than relying on either indicator alone.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C097-confirmation-principle|Confirmation Principle]]
