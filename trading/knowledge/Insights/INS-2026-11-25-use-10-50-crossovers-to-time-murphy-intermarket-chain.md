---
type: insight
date: 2026-11-25
actionability: 3
connection_type: creates_filter
domains: [indicators, intermarket_analysis, position_trading, trading_rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "EN028-10-and-50-day-moving-average-crossover"]
seed_id: commodity_inflation_stock
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: Murphy - Technical Analysis of the Financial Markets
---
# Use 10/50 crossovers to time Murphy intermarket chain

## Discovery Summary

N039 and EN028 both define a 10/50 moving-average crossover signal for stocks. The seed question adds Murphy's intermarket chain: commodities → bonds → stocks. Applying the same 10/50 crossover to commodity and bond proxies turns the chain into a sequence of trend-confirmation filters: a stock crossover signal is stronger when the earlier chain links have already crossed in the expected direction. This makes the intermarket chain actionable for position trading timeframes rather than a conceptual relationship.

## Trading Implication

Before acting on a 10/50 crossover in a stock index or individual stock, check the 10/50 crossover state of commodity and bond markets; take the stock signal only if it is aligned with the direction implied by the intermarket chain.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**creates_filter** — Actionability score: 3/5
