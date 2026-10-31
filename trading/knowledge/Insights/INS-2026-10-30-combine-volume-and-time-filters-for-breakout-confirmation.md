---
type: insight
date: 2026-10-30
actionability: 3
connection_type: adds_condition
domains: [patterns, rules, trendline analysis]
sources: ["EN008-volume-confirmation-at-pattern-completion", "EN008-volume-confirmation-at-pattern-completion", "R012-time-filter-for-trendline-breaks-two-day-rule"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Combine Volume and Time Filters for Breakout Confirmation

## Discovery Summary

EN008-volume-confirmation-at-pattern-completion requires a noticeable volume increase at pattern completion to validate a breakout, while R012-time-filter-for-trendline-breaks-two-day-rule demands a two-day close beyond the trendline. These two independent filters can be combined to create a more robust entry signal: only act when a breakout shows both volume expansion and persistence over two days, reducing false positives.

## Trading Implication

Traders should require both volume expansion and a two-day confirmation before entering on a pattern or trendline breakout, rather than relying on either signal alone.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[EN008-volume-confirmation-at-pattern-completion]]
- [[R012-time-filter-for-trendline-breaks-two-day-rule]]

## Connection Type

**adds_condition** — Actionability score: 3/5
