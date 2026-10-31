---
type: insight
date: 2026-10-18
actionability: 4
connection_type: adds_condition
domains: [trendline break rule, volume confirmation rule]
sources: ["EN008-volume-confirmation-at-pattern-completion", "EN008-volume-confirmation-at-pattern-completion", "R012-time-filter-for-trendline-breaks-two-day-rule"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume confirmation with two-day trendline break

## Discovery Summary

Combining EN008's requirement for volume increase at pattern completion with R012's two-day rule for trendline breaks creates a stronger filter: a trendline break is only valid if price closes beyond the trendline for two consecutive days and the second day's close shows increased volume. This reduces false breakouts.

## Trading Implication

Add volume confirmation to the two-day rule: only enter on a trendline break when the second close is accompanied by volume above the recent average.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[EN008-volume-confirmation-at-pattern-completion]]
- [[R012-time-filter-for-trendline-breaks-two-day-rule]]

## Connection Type

**adds_condition** — Actionability score: 4/5
