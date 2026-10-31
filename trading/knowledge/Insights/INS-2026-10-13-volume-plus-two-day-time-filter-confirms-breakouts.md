---
type: insight
date: 2026-10-13
actionability: 3
connection_type: creates_filter
domains: [pattern_completion, time_filter, trading_rules, trendline_breaks, volume_confirmation]
sources: ["EN008-volume-confirmation-at-pattern-completion", "EN008-volume-confirmation-at-pattern-completion", "R012-time-filter-for-trendline-breaks-two-day-rule"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume plus two-day time filter confirms breakouts

## Discovery Summary

EN008 requires noticeable volume expansion at pattern completion to validate reversals, while R012 adds a two-day time filter for trendline breaks. Combining these two independent confirmations means a breakout is acted on only after price holds beyond the level for two days and volume expands, filtering out premature and false signals.

## Trading Implication

Traders should wait for both the volume expansion described in EN008 and the two-day close rule from R012 before entering, rather than trading the first break. This reduces early-stop risk and improves breakout reliability.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[EN008-volume-confirmation-at-pattern-completion]]
- [[R012-time-filter-for-trendline-breaks-two-day-rule]]

## Connection Type

**creates_filter** — Actionability score: 3/5
