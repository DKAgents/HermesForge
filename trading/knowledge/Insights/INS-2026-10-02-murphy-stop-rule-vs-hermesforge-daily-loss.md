---
type: insight
date: 2026-10-02
actionability: 4
connection_type: adds_condition
domains: [risk_guidelines, trading_rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "EN028-10-and-50-day-moving-average-crossover", "RG033-handling-drawdowns-and-losing-streaks"]
seed_id: drawdown_system_shutdown
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: Murphy - Technical Analysis of the Financial Markets
---
# Murphy stop rule vs HermesForge daily loss

## Discovery Summary

Murphy's rule to stop trading a system when it consistently fails is not directly quantified in the crossover notes or risk guidelines. The HermesForge RISK_RULES daily loss limits provide a concrete stop-trading threshold, adding a specific condition to Murphy's general advice: halt trading after exceeding a preset daily loss limit until the system regime is reassessed.

## Trading Implication

Combine Murphy's concept of system failure with a hard daily loss cap from HermesForge: stop trading immediately if the daily loss limit is breached, and do not resume until the 10/50 crossover system is re-evaluated for continued viability.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[EN028-10-and-50-day-moving-average-crossover]]
- [[RG033-handling-drawdowns-and-losing-streaks]]

## Connection Type

**adds_condition** — Actionability score: 4/5
