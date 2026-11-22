---
type: insight
date: 2026-11-21
actionability: 3
connection_type: creates_filter
domains: [moving_average_oscillators, trend_vs_ranging_regime, triple_crossover_rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Use oscillator spread to filter triple crossover whipsaws in ranging markets

## Discovery Summary

The triple crossover method (R323 and N037, specifically the 4-9-18 day combination) is a trend-following entry rule, but it gives no explicit regime guard against sideways or choppy conditions. C128 reframes a double MA crossover as an oscillator, such as MACD, which directly reveals whether the moving averages are expanding, contracting, or crossing zero. That oscillator state can serve as a regime filter: when the MA spread is flat or oscillating around zero, the conditions needed for a reliable 4/9/18 triple crossover signal are absent.

## Trading Implication

Take triple crossover signals only when the corresponding MA oscillator is on the same side of zero and expanding, and skip signals while the oscillator is flat or repeatedly crossing zero to avoid whipsaws in ranging markets.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
