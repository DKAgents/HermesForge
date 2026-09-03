---
type: insight
date: 2026-09-03
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
---

# Volume-Confirmed Flag and Pennant Breakout Filter

## Discovery Summary

N043 notes that flags and pennants require a volume surge at trend resumption, while R082 and N013 establish that all valid breakouts must have heavy volume to avoid false signals. Combining these, a flag or pennant pattern that triggers a breakout without a clear volume spike fails two separate validation rules simultaneously, making it a higher-probability false breakout. The characteristic light-volume pause phase of flags/pennants makes the subsequent volume surge at breakout a non-negotiable confirmation element rather than just a general guideline.

## Trading Implication

Only enter a flag or pennant breakout if the breakout bar's volume is clearly above the declining volume baseline established during the one-to-three-week consolidation; if volume remains light, treat it as a bull trap and wait for a heavy-volume close beyond the pattern boundary.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**creates_filter** — Actionability score: 4/5
