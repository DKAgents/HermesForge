---
type: insight
date: 2026-11-20
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, risk_guidelines, rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume-confirmed flag/pennant breakouts determine stop tightening

## Discovery Summary

N043 flag/pennant characteristics treat light volume during the consolidation as normal, with the trend valid only if it resumes on a burst of volume. R082 and N013 both require heavy volume at the breakout and warn that a light-volume breakout is suspect, especially if followed by a heavy-volume decline. Therefore, a volume/price divergence during the pennant/flag pause is not a stop signal, but failure of volume to expand at the breakout should trigger tighter stops.

## Trading Implication

Do not tighten stops just because volume dries up while a flag/pennant forms; wait for the breakout. If the breakout has light volume, tighten stops, and if price then declines on heavy volume, exit rather than expecting continuation.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**creates_filter** — Actionability score: 4/5
