---
type: insight
date: 2026-10-29
actionability: 3
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["EN008-volume-confirmation-at-pattern-completion", "EN008-volume-confirmation-at-pattern-completion", "R012-time-filter-for-trendline-breaks-two-day-rule"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume + Time Filter Confirms Breakouts

## Discovery Summary

EN008-volume-confirmation-at-pattern-completion requires noticeable volume increase at pattern completion to validate breakouts. R012-time-filter-for-trendline-breaks-two-day-rule demands price hold beyond a trendline for two days. Combining these conditions creates a dual-filter that reduces false breakouts by requiring both volume confirmation and time confirmation before entry.

## Trading Implication

When a trendline breaks, do not enter until you see both a volume spike on the break and price closes beyond the trendline for two consecutive days.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[EN008-volume-confirmation-at-pattern-completion]]
- [[R012-time-filter-for-trendline-breaks-two-day-rule]]

## Connection Type

**creates_filter** — Actionability score: 3/5
