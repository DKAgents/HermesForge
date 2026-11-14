---
type: insight
date: 2026-11-13
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, trading_rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume-Confirmed Breakouts: Adjust Stops on Light-Volume Flags

## Discovery Summary

N043 shows flags/pennants pause on light volume and must resume on heavy volume. R082 and N013 both confirm that valid breakouts require heavy volume, while light-volume breakouts are likely false bull traps. Therefore, a flag/pennant breakout on light volume is a failed signal that warrants immediate stop tightening or exit, especially if a heavy-volume decline follows.

## Trading Implication

Wait for heavy volume on any flag/pennant breakout. If volume is light, treat the breakout as false, tighten stops below the pattern, and exit on any subsequent heavy-volume decline.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**adds_condition** — Actionability score: 4/5
