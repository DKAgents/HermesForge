---
type: insight
date: 2026-10-01
actionability: 4
connection_type: adds_condition
domains: [concepts, risk-guidelines, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "RG017-overboughtoversold-readings-in-strong-trends"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
---

# Secondary trends filter oscillator entries in strong trends

## Discovery Summary

C366-secondary-trends identifies counter-trend corrections within a larger primary trend. EN041-oscillator-entry-strategy-in-trending-markets likely uses oscillator signals to time entries in the direction of that primary trend, often during secondary pullbacks. RG017-overboughtoversold-readings-in-strong-trends warns that extreme oscillator readings are unreliable for counter-trend trades. The connection is that the risk guideline adds a condition to the entry rule: oscillator signals must align with the primary trend, and secondary trends provide the optimal entry window.

## Trading Implication

In a strong uptrend, do not short based on overbought oscillator readings; instead, wait for a secondary pullback to trigger a long oscillator entry, ensuring alignment with the primary trend and avoiding counter-trend trades.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[RG017-overboughtoversold-readings-in-strong-trends]]

## Connection Type

**adds_condition** — Actionability score: 4/5
