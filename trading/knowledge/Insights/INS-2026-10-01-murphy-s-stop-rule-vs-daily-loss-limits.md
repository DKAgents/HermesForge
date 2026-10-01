---
type: insight
date: 2026-10-01
actionability: 3
connection_type: contradicts_assumption
domains: [indicators, risk-guidelines, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "EN028-10-and-50-day-moving-average-crossover", "RG033-handling-drawdowns-and-losing-streaks"]
seed_id: drawdown_system_shutdown
tags: [insight, discovery, knowledge-evolution]
---

# Murphy's stop rule vs daily loss limits

## Discovery Summary

Murphy's rule (from 'EN028-10-and-50-day-moving-average-crossover' or similar) traditionally halts trading after a fixed number of consecutive losses or a drawdown threshold, while HermesForge's RG033 'Handling Drawdowns and Losing Streaks' likely imposes a hard daily loss limit. The conflict is that a daily loss cap might trigger a stop earlier than Murphy's system-level rule, or vice versa, forcing a decision on which has priority.

## Trading Implication

Traders must predefine a hierarchy: either the daily loss limit overrides Murphy's system stop (so a losing day halts everything) or Murphy's rule takes precedence (allowing continued trading within the day until its own stop is hit). Choosing the wrong order can worsen drawdowns.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[EN028-10-and-50-day-moving-average-crossover]]
- [[RG033-handling-drawdowns-and-losing-streaks]]

## Connection Type

**contradicts_assumption** — Actionability score: 3/5
