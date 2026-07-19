---
type: insight
date: 2026-07-19
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
---

# Volume Divergence in Flags Signals Stop Tightening Opportunity

## Discovery Summary

N043 establishes that flags and pennants occur at the midpoint of a move and require very light volume during consolidation followed by a burst on resumption. R082 mandates that breakouts from all patterns must be accompanied by heavy volume to be valid. N013 adds the critical filter: a breakout on light volume followed by a subsequent decline on heavy volume is a 'negative chart combination' signaling a false breakout. Together, these three notes create a layered volume-confirmation protocol specific to continuation patterns: if the consolidation volume is not light AND the breakout volume is not heavy, the midpoint assumption in N043 is invalidated, and the trader is likely holding a failed pattern rather than a continuation.

## Trading Implication

When a flag or pennant breakout occurs on light volume (violating R082 and matching N013's false breakout signature), stops should be tightened immediately to just below the breakout bar rather than using the full flagpole-based target, since the midpoint-of-move thesis in N043 no longer holds.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**adds_condition** — Actionability score: 4/5
