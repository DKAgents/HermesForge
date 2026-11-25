---
type: insight
date: 2026-11-24
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, risk guidelines, trading rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Tighten Stops on Light-Volume Breakouts After Flags/Pennants

## Discovery Summary

N043 shows flags/pennants pause on light volume and should resume on a heavy-volume burst. R082 confirms all valid pattern breakouts need heavy volume, and N013 warns that a light-volume upside breakout is likely false, especially if a heavy-volume decline follows. Therefore, a light-volume breakout from a flag/pennant is a price/volume divergence that should trigger immediate stop tightening rather than assuming the continuation is valid.

## Trading Implication

When a flag or pennant breaks out on light volume, move stops from below the pattern to just below the breakout price; exit if heavy-volume selling follows the failed breakout.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**adds_condition** — Actionability score: 4/5
