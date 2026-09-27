---
type: insight
date: 2026-08-18
actionability: 3
connection_type: adds_condition
domains: [indicators, intermarket_analysis, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "EN028-10-and-50-day-moving-average-crossover"]
seed_id: commodity_inflation_stock
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# 10/50 MA Crossover as Intermarket Sequence Confirmation Entry

## Discovery Summary

EN028 and N039 both describe the same 10/50 day MA crossover rule for stocks, confirming it as a well-established mechanical entry signal. The seed question introduces Murphy's intermarket chain (commodities → bonds → stocks), which suggests that a 10/50 MA buy signal in stocks gains higher probability when bonds are already in an uptrend (yields falling) and commodities have already turned — meaning the intermarket sequence has 'set up' before the stock crossover fires. Neither note references intermarket context, but the crossover rule from EN028/N039 can serve as the final-stage entry trigger within that sequence.

## Trading Implication

A trader should only act on a 10-day crossing above the 50-day in stocks when bonds are concurrently in an uptrend (confirming the intermarket chain is aligned), using the crossover as a timing entry rather than a standalone signal.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**adds_condition** — Actionability score: 3/5
