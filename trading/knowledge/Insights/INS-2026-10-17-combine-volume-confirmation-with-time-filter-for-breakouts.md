---
type: insight
date: 2026-10-17
actionability: 4
connection_type: creates_filter
domains: [trendline_time_filter, volume_confirmation]
sources: ["EN008-volume-confirmation-at-pattern-completion", "EN008-volume-confirmation-at-pattern-completion", "R012-time-filter-for-trendline-breaks-two-day-rule"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Combine volume confirmation with time filter for breakouts

## Discovery Summary

By merging EN008's volume confirmation requirement with R012's two-day rule for trendline breaks, traders can filter out false breakouts that lack either volume or sustained price action. This dual condition reduces whipsaws and improves entry reliability.

## Trading Implication

Enter a breakout only when the price closes beyond the trendline on increased volume and holds above or below for two consecutive days.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[EN008-volume-confirmation-at-pattern-completion]]
- [[R012-time-filter-for-trendline-breaks-two-day-rule]]

## Connection Type

**creates_filter** — Actionability score: 4/5
