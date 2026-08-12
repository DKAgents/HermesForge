---
type: insight
date: 2026-08-11
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N013-volume-as-a-filter-for-false-breakouts", "R052-filters-for-confirming-breakouts", "N028-bull-trap-false-upside-breakout"]
seed_id: breakout_volume_risk
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume-Confirmed Breakout Filter With Stop Placement Logic

## Discovery Summary

N013 and N028 together establish that light-volume breakouts followed by heavy-volume reversals are the signature of a bull trap, while R052 provides a multi-criteria confirmation framework (close-based, percentage, two-day, Friday close) that operates independently of volume. The non-obvious connection is that combining R052's structural filters with the volume signature from N013/N028 creates a compound confirmation rule: a breakout that fails R052's close-based or two-day criteria AND shows light volume on the break plus heavy volume on the reversal provides a high-confidence false-breakout identification. This compound signal also implicitly defines stop placement — the original breakout level becomes the logical stop for any short trade entered on the confirmed reversal.

## Trading Implication

When a breakout fails at least one R052 structural filter (e.g., no two consecutive closes above resistance) AND shows light volume on the breakout day followed by heavy volume decline, enter short with a stop just above the false breakout high, treating that level as the invalidation point.

## Supporting Notes

- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[R052-filters-for-confirming-breakouts]]
- [[N028-bull-trap-false-upside-breakout]]

## Connection Type

**creates_filter** — Actionability score: 4/5
