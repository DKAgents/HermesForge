---
type: insight
date: 2026-08-30
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
---

# Volume Confluence Filters Flag Breakout Traps

## Discovery Summary

The flag and pennant summary (N043) states that the consolidation phase occurs on very light volume and the trend resumption on a burst of trading activity. The breakout rule (R082) demands heavy volume for any valid breakout, while the false breakout filter (N013) warns that light-volume breakouts are likely bull traps. Together, they create a filter: a flag or pennant breakout on light volume is invalid and signals a potential false move.

## Trading Implication

Only trade flag or pennant breakouts accompanied by a clear volume surge. If the breakout occurs on light volume, place a tight stop just beyond the pattern's boundary to exit quickly if the breakout fails.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**creates_filter** — Actionability score: 4/5
