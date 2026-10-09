---
type: insight
date: 2026-10-08
actionability: 4
connection_type: resolves_conflict
domains: [edge-conditions, indicators, risk_guidelines, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "E020-double-crossover-reduces-whipsaws-vs-single-average", "EN028-10-and-50-day-moving-average-crossover"]
seed_id: diversification_position_limit
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: Murphy - Technical Analysis of the Financial Markets
---
# 10/50 Crossover Filters Murphy Limit Conflict

## Discovery Summary

The 10/50-day moving average crossover (N039, EN028) reduces whipsaws compared to a single moving average (E020). This filter resolves the apparent conflict between Murphy's 10-15% per market limit and HermesForge 1% position sizing by enabling tighter per-market exposure without risking multiple false signals — the crossover's lower whipsaw rate supports using a smaller per-trade size (1%) within a larger per-market limit (10-15%) without overexposing to noise.

## Trading Implication

A trader should apply the 10/50 crossover as a signal filter, allowing position sizing at 1% per trade while respecting the 10-15% per-market cap, since the crossover reduces the risk of successive whipsaws that would erode the position sizing buffer.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[E020-double-crossover-reduces-whipsaws-vs-single-average]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**resolves_conflict** — Actionability score: 4/5

## Related Notes
- [[EN026-single-moving-average-buy-and-sell-signals|Single Moving Average Buy and Sell Signals]]
