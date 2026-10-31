---
type: insight
date: 2026-10-14
actionability: 3
connection_type: adds_condition
domains: [rules]
sources: ["EN008-volume-confirmation-at-pattern-completion", "EN008-volume-confirmation-at-pattern-completion", "R012-time-filter-for-trendline-breaks-two-day-rule"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume spike plus time filter confirms breakouts

## Discovery Summary

EN008 requires a noticeable volume increase at pattern completion to validate a breakout, while R012 imposes a two-day wait after a trendline break to filter false moves. Combining these rules means a trader only acts when both conditions are met—volume spike on the breakout day and price still beyond the trendline two days later—providing a robust double confirmation.

## Trading Implication

Enter a position only after a pattern or trendline break shows a clear volume surge and the price holds its breakout level for two additional sessions, thereby reducing premature entries on weak or short-lived moves.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[EN008-volume-confirmation-at-pattern-completion]]
- [[R012-time-filter-for-trendline-breaks-two-day-rule]]

## Connection Type

**adds_condition** — Actionability score: 3/5
