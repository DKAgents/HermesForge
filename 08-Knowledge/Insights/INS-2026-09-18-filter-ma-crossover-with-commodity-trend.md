---
type: insight
date: 2026-09-18
actionability: 4
connection_type: adds_condition
domains: [edge-conditions, indicators, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "EN028-10-and-50-day-moving-average-crossover", "E040-commodity-exporters-and-deflation-risk"]
seed_id: commodity_inflation_stock
tags: [insight, discovery, knowledge-evolution]
---

# Filter MA crossover with commodity trend

## Discovery Summary

The 10/50-day moving average crossover (N039, EN028) provides trend signals for equity markets. The commodity exporter risk note (E040) highlights that falling commodity prices can damage economies like Australia and Canada. Combining these, a trader can filter out buy signals from the MA crossover on commodity-exporting country ETFs when commodity prices are in a downtrend, avoiding false signals during macro headwinds.

## Trading Implication

When trading ETFs for commodity-exporting nations (e.g., EWA, EWC), only act on 10/50-day crossover buy signals if the commodity index (e.g., CRB) is above its 200-day moving average; ignore or short sell signals during commodity downtrends.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[EN028-10-and-50-day-moving-average-crossover]]
- [[E040-commodity-exporters-and-deflation-risk]]

## Connection Type

**adds_condition** — Actionability score: 4/5
