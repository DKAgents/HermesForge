---
type: insight
date: 2026-08-04
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

C149 establishes that RSI and Stochastics confirm each other most powerfully when simultaneously in extreme territory. R177 states that any oscillator in its presignal (overbought/oversold) zone can filter candle reversal patterns for validity. N165 defines RSI's specific thresholds (>70 overbought, <30 oversold). Combining these: a candle reversal pattern gains the strongest confirmation when BOTH RSI crosses its 70/30 threshold AND Stochastics is simultaneously in overbought/oversold territory — a dual-oscillator gate that is stricter than using either alone.

## Trading Implication

A trader should only act on candle reversal patterns when both RSI (using 70/30 thresholds per N165) AND Stochastics are simultaneously in overbought or oversold territory, per C149's confirmation principle applied through R177's filtering framework — reducing false reversals at the cost of fewer signals.

## Supporting Notes

- [[C149-rsi-vs-stochastics-volatility-comparison]]
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]]
- [[R177-filtered-candle-patterns-oscillator-alternatives]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[C097-confirmation-principle|Confirmation Principle]]
