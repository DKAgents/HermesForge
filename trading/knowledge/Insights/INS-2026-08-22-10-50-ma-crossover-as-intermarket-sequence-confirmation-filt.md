---
type: insight
date: 2026-08-22
actionability: 3
connection_type: creates_filter
domains: [indicators, intermarket_analysis, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "EN028-10-and-50-day-moving-average-crossover"]
seed_id: commodity_inflation_stock
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# 10/50 MA Crossover as Intermarket Sequence Confirmation Filter

## Discovery Summary

EN028 and N039 both define the same 10/50 MA crossover rule for stocks, confirming internal consistency. The seed question introduces Murphy's intermarket chain (commodities → bonds → stocks), suggesting that stock buy signals from the 10/50 crossover (EN028/N039) could be filtered by requiring prior confirmation in the bond market — i.e., only act on the 10-day crossing above the 50-day in stocks when bonds are already in an uptrend. This sequences the intermarket chain into the crossover entry trigger, reducing false signals.

## Trading Implication

A trader should only take the 10/50 MA stock buy signal when bonds (e.g., TLT or 10-year futures) are also above their own 50-day MA, applying the intermarket chain as a prerequisite filter before entering stock positions.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**creates_filter** — Actionability score: 3/5
