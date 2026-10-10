---
type: insight
date: 2026-10-10
actionability: 4
connection_type: creates_filter
domains: [rules]
sources: ["EN008-volume-confirmation-at-pattern-completion", "EN008-volume-confirmation-at-pattern-completion", "R012-time-filter-for-trendline-breaks-two-day-rule"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume + time filter for trendline breaks

## Discovery Summary

The two-day rule (R012) provides a time-based confirmation for trendline breaks, while volume confirmation (EN008) ensures the breakout has strong participation. Combining them filters out weak breakouts that lack either sustained price action or volume, reducing false signals.

## Trading Implication

Only take a trendline breakout trade after price closes beyond the line for two consecutive days AND volume is noticeably higher on the second close.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[EN008-volume-confirmation-at-pattern-completion]]
- [[R012-time-filter-for-trendline-breaks-two-day-rule]]

## Connection Type

**creates_filter** — Actionability score: 4/5
