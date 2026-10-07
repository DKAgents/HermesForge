---
type: insight
date: 2026-10-07
actionability: 4
connection_type: adds_condition
domains: [concepts, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
---

# Secondary trend oscillator entry amplifies countertrend risk

## Discovery Summary

C366-secondary-trends defines a secondary trend as a corrective move against the primary trend, which often produces false signals for oscillators. EN041-oscillator-entry-strategy-in-trending-markets involves entering on oscillator signals in the direction of the primary trend. When an oscillator triggers a counter-trend entry during a secondary move, it violates the rule's intent, requiring an additional condition to filter out entries that align with the secondary trend rather than the primary trend.

## Trading Implication

A trader should avoid oscillator-based entries that are in the direction of a secondary trend (i.e., counter to the primary trend) unless a separate risk rule confirms the trade has a favorable risk-reward ratio for a countertrend position.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]

## Connection Type

**adds_condition** — Actionability score: 4/5
