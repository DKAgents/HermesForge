---
type: insight
date: 2026-08-23
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume Validates Gap Type: Chase vs Fade Decision Rule

## Discovery Summary

N150 and C328 identify gap types with opposing implications (breakaway/runaway = chase; exhaustion = fade), but neither provides a real-time filter to distinguish them. R082 supplies the missing discriminator: volume. A breakaway gap accompanied by heavy volume (per R082's breakout rule) confirms a new trend to chase, while a gap on declining or average volume is more likely a common or exhaustion gap to fade. The island reversal pattern in N150 — where an exhaustion gap is followed by a breakaway gap — would require two volume confirmations to validate the full reversal.

## Trading Implication

When a gap forms, immediately check volume: a gap on surging volume signals a breakaway or runaway gap to enter in the gap's direction; a gap on normal or declining volume should be treated as a common or exhaustion gap and faded or ignored.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[N144-island-reversal-pattern|Island Reversal Pattern]]
