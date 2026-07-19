---
type: insight
date: 2026-07-19
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
---

# Volume-Confirmed Flag/Pennant Breakout as False-Signal Filter

## Discovery Summary

N043 establishes that flags and pennants form on very light volume during consolidation and resume on a burst of activity — this volume signature is a structural characteristic of the pattern itself. R082 states that all pattern breakouts require heavy volume to be considered valid, while N013 specifies that a breakout on light volume followed by a decline on heavy volume is a 'bull trap' combination. Together, these three notes create a two-stage volume test specific to flag/pennant trades: (1) confirm volume contracts meaningfully during the 1-3 week consolidation phase, and (2) require a volume surge at the breakout — treating any breakout on light volume as presumptively false regardless of price action.

## Trading Implication

A trader should only enter a flag or pennant breakout if volume during the consolidation is visibly below the flagpole average AND volume on the breakout bar exceeds that consolidation average; if the breakout occurs on low volume, wait for either a volume-confirmed re-test or exit quickly if a high-volume decline follows.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**creates_filter** — Actionability score: 4/5
