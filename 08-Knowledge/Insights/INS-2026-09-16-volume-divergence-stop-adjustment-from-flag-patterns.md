---
type: insight
date: 2026-09-16
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume divergence stop adjustment from flag patterns

## Discovery Summary

Flag and pennant patterns require light volume during consolidation and heavy volume on breakout (N043-flag-and-pennant-summary-characteristics, R082-breakouts-must-be-accompanied-by-heavy-volume). If volume diverges—e.g., heavy volume during the pause or light volume on breakout—it signals a false move, which N013-volume-as-a-filter-for-false-breakouts warns against. This creates a specific stop adjustment rule: tighten or exit when volume fails to confirm the pattern's expected behavior.

## Trading Implication

During a flag or pennant, place a stop just beyond the opposite side of the pattern if volume during the consolidation or breakout diverges from the expected light-then-heavy sequence, to exit before a false breakout.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**creates_filter** — Actionability score: 4/5
