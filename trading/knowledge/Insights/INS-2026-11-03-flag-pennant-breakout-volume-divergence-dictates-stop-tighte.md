---
type: insight
date: 2026-11-03
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, trading rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Flag/Pennant Breakout Volume Divergence Dictates Stop Tightening

## Discovery Summary

N043 describes flags/pennants as pausing on light volume after a heavy-volume pole, then resuming on a burst of volume. R082 requires heavy volume at all pattern breakouts, and N013 warns that a light-volume breakout is likely false, especially if a heavy-volume decline follows. Together, these notes create a filter: in a flag/pennant, the breakout's volume determines whether the continuation signal is valid and whether stops should be held or tightened.

## Trading Implication

In a flag/pennant within an existing trend, wait for the breakout volume: if volume expands, keep the position with a normal stop; if volume is light or price then falls on heavy volume, tighten stops or exit because the continuation signal is likely false.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**creates_filter** — Actionability score: 4/5
