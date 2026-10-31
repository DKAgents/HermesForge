---
type: insight
date: 2026-10-12
actionability: 4
connection_type: creates_filter
domains: [rules: time filter, rules: volume confirmation]
sources: ["EN008-volume-confirmation-at-pattern-completion", "EN008-volume-confirmation-at-pattern-completion", "R012-time-filter-for-trendline-breaks-two-day-rule"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume and time filter for trendline breaks

## Discovery Summary

Combining EN008's volume confirmation rule (breakout must show increased volume) with R012's two-day rule (break must hold for two consecutive closes) creates a stronger filter for trendline breakouts. Individually, each rule reduces false signals; together they require both momentum and persistence, significantly improving reliability.

## Trading Implication

When a trendline breaks, enter only if volume spikes above average on the breakout day and price closes beyond the line on two consecutive days.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[EN008-volume-confirmation-at-pattern-completion]]
- [[R012-time-filter-for-trendline-breaks-two-day-rule]]

## Connection Type

**creates_filter** — Actionability score: 4/5
