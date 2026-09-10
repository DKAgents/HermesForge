---
type: insight
date: 2026-09-10
actionability: 4
connection_type: creates_filter
domains: [edge-conditions, indicators, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "EN028-10-and-50-day-moving-average-crossover", "E040-commodity-exporters-and-deflation-risk"]
seed_id: commodity_inflation_stock
tags: [insight, discovery, knowledge-evolution]
---

# Commodity 10/50 Crossover Stocks Filter

## Discovery Summary

The 10/50-day moving average crossover method from N039 and EN028, typically applied to stocks, can be shifted to commodity prices to filter equity trades in commodity-exporting nations. E040 notes that plunging commodity prices damage countries like Australia, Canada, Mexico, and Russia. By applying the 10/50 crossover to a commodity index, traders can generate early trend signals for these nations' equity markets, following Murphy's intermarket logic that commodities lead stocks.

## Trading Implication

Only take 10/50 crossover buy signals on country ETFs or indices of commodity exporters (e.g., EWA, EWC) when the commodity price's 10-day MA is above its 50-day MA; avoid or exit when the commodity 10/50 crosses down.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[EN028-10-and-50-day-moving-average-crossover]]
- [[E040-commodity-exporters-and-deflation-risk]]

## Connection Type

**creates_filter** — Actionability score: 4/5
