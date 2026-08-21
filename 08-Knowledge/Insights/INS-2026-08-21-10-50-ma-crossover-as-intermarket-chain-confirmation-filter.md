---
type: insight
date: 2026-08-21
actionability: 3
connection_type: creates_filter
domains: [indicators, intermarket_analysis, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "EN028-10-and-50-day-moving-average-crossover"]
seed_id: commodity_inflation_stock
tags: [insight, discovery, knowledge-evolution]
---

# 10/50 MA Crossover as Intermarket Chain Confirmation Filter

## Discovery Summary

Both N039 and EN028 redundantly confirm the 10/50 day MA crossover rules for stocks. The seed question introduces Murphy's intermarket chain (commodities → bonds → stocks), which provides a macro-sequencing context that is absent from both notes. A non-obvious connection emerges: the 10/50 crossover signal in stocks could be filtered or confirmed by the state of the commodities→bonds intermarket chain — only taking stock buy signals (10-day crossing above 50-day per EN028) when the intermarket chain is constructive (rising bonds signaling falling inflation/rates, supportive for equities).

## Trading Implication

Before acting on a 10/50 MA stock buy signal, confirm that the intermarket chain is aligned (e.g., bonds trending up or stabilizing, commodities not spiking adversely); skip or delay the stock entry if bonds are in a downtrend driven by commodity pressure.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**creates_filter** — Actionability score: 3/5
