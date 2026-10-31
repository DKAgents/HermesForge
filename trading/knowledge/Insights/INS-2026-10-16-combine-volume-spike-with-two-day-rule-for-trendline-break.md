---
type: insight
date: 2026-10-16
actionability: 4
connection_type: adds_condition
domains: [trading_rules]
sources: ["EN008-volume-confirmation-at-pattern-completion", "EN008-volume-confirmation-at-pattern-completion", "R012-time-filter-for-trendline-breaks-two-day-rule"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Combine volume spike with two-day rule for trendline break

## Discovery Summary

EN008-volume-confirmation-at-pattern-completion requires a volume increase at pattern completion. R012-time-filter-for-trendline-breaks-two-day-rule mandates waiting two days to confirm a trendline break. Combining both creates a stronger filter: require a volume spike on the initial break day, then hold for two more days before entry, reducing false breakouts.

## Trading Implication

When a trendline is broken, wait for a volume spike on the break day and then confirm the breakout holds for two additional days before entering a position.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[EN008-volume-confirmation-at-pattern-completion]]
- [[R012-time-filter-for-trendline-breaks-two-day-rule]]

## Connection Type

**adds_condition** — Actionability score: 4/5
