---
type: insight
date: 2026-09-21
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, indicators, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "EN028-10-and-50-day-moving-average-crossover", "C128-moving-averages-as-oscillators-via-double-crossover"]
seed_id: drawdown_system_shutdown
tags: [insight, discovery, knowledge-evolution]
---

# Double Crossover Oscillator Confirms Murphy’s Stop Trading Point

## Discovery Summary

The double crossover method (10/50) is traditionally a trend-following signal, but the conceptual note reveals it can also function as an oscillator via the spread between the two moving averages, effectively the core of MACD. Murphy’s rule to stop trading a system when it fails (e.g., after a string of losing signals) aligns with the oscillator losing its momentum—when the spread stops expanding or reverses despite price, the system’s edge is fading. This creates a concrete rule: monitor the 10/50 spread as an oscillator; when it diverges from price or fails to make new highs/lows, flatten positions and stand aside until the crossover reestablishes a healthy trend.

## Trading Implication

Traders should not blindly follow 10/50 crossovers—treat the spread as a gauge of system health; if the spread diverges from price or oscillates near zero after a prolonged trend, reduce risk and wait for confirmed re-expansion before re-entering.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[EN028-10-and-50-day-moving-average-crossover]]
- [[C128-moving-averages-as-oscillators-via-double-crossover]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
