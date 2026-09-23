---
type: insight
date: 2026-09-20
actionability: 4
connection_type: adds_condition
domains: [edge-conditions, indicators, risk-management, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "E020-double-crossover-reduces-whipsaws-vs-single-average", "EN028-10-and-50-day-moving-average-crossover"]
seed_id: diversification_position_limit
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Double Crossover and 1% Position Sizing Interplay

## Discovery Summary

The 10/50-day double crossover (N039, EN028) generates signals with fewer whipsaws but more lag (E020). When combined with HermesForge's 1% position sizing rule, the crossover acts as a risk filter: the reduced whipsaw frequency means the 1% risk per trade is less likely to be churned by false signals, while the lag inherent in the crossover means the 1% stop-loss should be calibrated to the average true range of the 50-day MA to avoid premature exits during normal pullbacks. This connection is non-trivial because it integrates a technical signal's reliability characteristics with a fixed fractional risk management rule.

## Trading Implication

When using the 10/50 crossover, apply HermesForge's 1% risk per trade, but set your stop-loss based on the distance from the 50-day MA (e.g., 1.5x ATR) to accommodate the lag, and only take signals that align with the direction of the 50-day slope to reduce counter-trend trades.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[E020-double-crossover-reduces-whipsaws-vs-single-average]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[N140-average-true-range-atr-definition|Average True Range (ATR) Definition]]
