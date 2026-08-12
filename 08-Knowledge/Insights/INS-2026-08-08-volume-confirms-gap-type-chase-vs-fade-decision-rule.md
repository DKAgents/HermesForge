---
type: insight
date: 2026-08-08
actionability: 4
connection_type: creates_filter
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume Confirms Gap Type: Chase vs Fade Decision Rule

## Discovery Summary

N150 and C328 establish that gaps carry directional meaning based on type (breakaway=trend start, runaway=trend continuation, exhaustion=trend end), while R082 mandates that valid breakouts must be accompanied by heavy volume. Cross-applying R082's volume rule to gap classification creates a practical filter: a gap with surge volume signals a breakaway or runaway gap (chase), while a gap occurring on declining or normal volume after an extended trend is more likely an exhaustion gap (fade). Island reversals (exhaustion gap + opposite breakaway gap) from N150 represent the clearest fade setup when the second gap also carries volume.

## Trading Implication

A trader should enter in the direction of a gap only when accompanied by heavy volume — confirming breakaway or runaway type — and should fade or avoid gaps on thin volume late in a trend, treating them as probable exhaustion gaps. Island reversal patterns with volume confirmation on the second gap are high-conviction reversal entries.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
