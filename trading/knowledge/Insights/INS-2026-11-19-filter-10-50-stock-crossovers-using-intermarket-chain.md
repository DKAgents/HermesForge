---
type: insight
date: 2026-11-19
actionability: 4
connection_type: creates_filter
domains: [indicators, intermarket_analysis, position_trading, trading_rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "EN028-10-and-50-day-moving-average-crossover"]
seed_id: commodity_inflation_stock
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Filter 10/50 stock crossovers using intermarket chain

## Discovery Summary

N039 and EN028 both define a 10-day/50-day moving-average crossover as an intermediate-term stock trend signal. The seed question's intermarket chain (commodities → bonds → stocks) implies that commodity and bond trends lead stock trends. Applying the same 10/50 crossover to commodity and bond indexes creates a leading filter for stock crossover signals, since commodity strength tends to precede bond weakness and stock weakness.

## Trading Implication

Before taking a 10/50 crossover trade in stocks, check the 10/50 crossover direction of commodity and bond indexes and align the stock position with the intermarket chain direction.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**creates_filter** — Actionability score: 4/5
