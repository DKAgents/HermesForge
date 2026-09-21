---
type: insight
date: 2026-09-21
actionability: 4
connection_type: adds_condition
domains: [indicators, risk guidelines, trading rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "E020-double-crossover-reduces-whipsaws-vs-single-average", "EN028-10-and-50-day-moving-average-crossover"]
seed_id: diversification_position_limit
tags: [insight, discovery, knowledge-evolution]
---

# Crossover Confirms Position Sizing, Limits Not Conflict

## Discovery Summary

Murphy's 10-15% per market limit (from seed) and HermesForge's 1% risk per trade are complementary position sizing rules; the 10/50-day crossover acts as a timing filter that should trigger entries/exits. The crossover's reduced whipsaws (E020) make the 1% risk rule more effective because fewer false signals mean less capital eroded by stop-outs, while Murphy's limit caps total exposure per market even as signals may be repeated.

## Trading Implication

Apply both position sizing rules simultaneously: risk no more than 1% per trade and no more than 10-15% of capital in any single market, but only take the trade when the 10/50 crossover gives a fresh signal. This ensures the crossover's reliability improves position sizing discipline.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[E020-double-crossover-reduces-whipsaws-vs-single-average]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**adds_condition** — Actionability score: 4/5
