---
type: insight
date: 2026-09-28
actionability: 4
connection_type: adds_condition
domains: [indicators, risk-guidelines, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "EN028-10-and-50-day-moving-average-crossover", "RG033-handling-drawdowns-and-losing-streaks"]
seed_id: drawdown_system_shutdown
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: Murphy - Technical Analysis of the Financial Markets
---
# Murphy's 3-loss stop complements HermesForge daily risk limits

## Discovery Summary

Murphy's guideline is to stop trading a system after three consecutive losing trades; RG033 handling drawdowns/losing streaks formalizes this as a drawdown control for the N039/EN028 10-and-50-day crossover method. HermesForge RISK_RULES daily loss limits add a second, independent shutdown condition that can trigger before the three-loss streak completes. The 10/50 crossover signal should therefore be acted on only when neither risk threshold has been hit.

## Trading Implication

Before acting on the next EN028 10/50 crossover, check for three consecutive system losses and HermesForge daily loss limit; if either is breached, stand aside until the risk condition resets.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[EN028-10-and-50-day-moving-average-crossover]]
- [[RG033-handling-drawdowns-and-losing-streaks]]

## Connection Type

**adds_condition** — Actionability score: 4/5
