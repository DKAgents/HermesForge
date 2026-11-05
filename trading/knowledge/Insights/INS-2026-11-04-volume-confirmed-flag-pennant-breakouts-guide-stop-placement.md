---
type: insight
date: 2026-11-04
actionability: 4
connection_type: adds_condition
domains: [breakout rules, patterns, volume indicators]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume-Confirmed Flag/Pennant Breakouts Guide Stop Placement

## Discovery Summary

N043 flag/pennant summary requires a light-volume pause followed by a heavy-volume trend resumption, while R082 and N013 state that valid breakouts need heavy volume and light-volume breakouts can be false. Thus a flag/pennant breakout on light volume fails the pattern's own condition; a subsequent heavy-volume decline after such a breakout is a negative signal. This transforms a generic volume rule into a specific stop-adjustment trigger for continuation patterns.

## Trading Implication

On a flag/pennant, do not trail stops aggressively until the breakout prints heavy volume. If the breakout is light-volume and then price falls on heavy volume, tighten or exit stops immediately because the continuation likely failed.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**adds_condition** — Actionability score: 4/5
