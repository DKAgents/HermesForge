---
type: insight
date: 2026-08-18
actionability: 3
connection_type: creates_filter
domains: [concepts, indicators, rules]
sources: ["C128-moving-averages-as-oscillators-via-double-crossover", "R323-triple-crossover-method-moving-averages", "N037-triple-crossover-method-4-9-18-day-moving-average"]
seed_id: pattern_regime
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Triple Crossover Oscillator Gap Reveals Regime Filter Logic

## Discovery Summary

C128 establishes that two-MA differences can be expressed as oscillators (MACD-style), revealing trend strength via spread magnitude. R323 and N037 extend this to three MAs (specifically 4-9-18 day), where the sequential crossover logic implies two oscillator gaps (4-9 spread and 9-18 spread) must align for a confirmed signal. In ranging or volatile markets, these two spreads will oscillate without directional alignment, causing frequent false crossovers — exactly the failure mode the seed question targets. The 4-9 gap oscillating near zero while the 9-18 gap remains flat is a detectable ranging-regime signature.

## Trading Implication

A trader should require both the 4-9 spread and the 9-18 spread (viewed as oscillators per C128) to be directionally aligned and expanding before acting on a 4-9-18 triple crossover signal; if either spread is contracting or near zero, treat the market as ranging and suppress the trade.

## Supporting Notes

- [[C128-moving-averages-as-oscillators-via-double-crossover]]
- [[R323-triple-crossover-method-moving-averages]]
- [[N037-triple-crossover-method-4-9-18-day-moving-average]]

## Connection Type

**creates_filter** — Actionability score: 3/5
