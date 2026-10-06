---
type: insight
date: 2026-10-06
actionability: 3
connection_type: adds_condition
domains: [rules]
sources: ["EN008-volume-confirmation-at-pattern-completion", "EN008-volume-confirmation-at-pattern-completion", "R012-time-filter-for-trendline-breaks-two-day-rule"]
seed_id: vol_confirm_risk
tags: [insight, discovery, knowledge-evolution]
---

# Volume + Time Filter for Trendline Breaks

## Discovery Summary

EN008-volume-confirmation-at-pattern-completion requires volume increase at breakout, while R012-time-filter-for-trendline-breaks-two-day-rule adds a waiting period. Combining both filters on trendline breaks reduces false breakouts by ensuring both price confirmation (two days) and volume confirmation (at break).

## Trading Implication

When a trendline is broken, wait for two consecutive closes beyond it and confirm with a noticeable volume spike on the first break day before entering.

## Supporting Notes

- [[EN008-volume-confirmation-at-pattern-completion]]
- [[EN008-volume-confirmation-at-pattern-completion]]
- [[R012-time-filter-for-trendline-breaks-two-day-rule]]

## Connection Type

**adds_condition** — Actionability score: 3/5
