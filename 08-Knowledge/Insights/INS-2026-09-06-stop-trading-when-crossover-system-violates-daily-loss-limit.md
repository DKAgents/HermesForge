---
type: insight
date: 2026-09-06
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "EN028-10-and-50-day-moving-average-crossover", "C128-moving-averages-as-oscillators-via-double-crossover"]
seed_id: drawdown_system_shutdown
tags: [insight, discovery, knowledge-evolution]
---

# Stop trading when crossover system violates daily loss limits

## Discovery Summary

The double crossover method using 10-day and 50-day moving averages (N039, EN028) generates buy and sell signals for intermediate-term stock trends. The concept note C128 frames this crossover as an oscillator-like construct, comparing the difference between two moving averages. When the SHOT stops generating signals that align with a trader's daily loss limits from risk rules, the system should be halted — the crossover method's effectiveness as an oscillator-based approach degrades during choppy markets, making it critical to overlay a daily loss limit that triggers a stop-trading condition when the 10/50 cross produces consecutive whipsaw losses.

## Trading Implication

A trader should cease taking new 10/50 crossover signals for the remainder of any trading day once the daily loss limit is hit, regardless of whether a fresh crossover buy or sell signal appears.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[EN028-10-and-50-day-moving-average-crossover]]
- [[C128-moving-averages-as-oscillators-via-double-crossover]]

## Connection Type

**adds_condition** — Actionability score: 4/5
