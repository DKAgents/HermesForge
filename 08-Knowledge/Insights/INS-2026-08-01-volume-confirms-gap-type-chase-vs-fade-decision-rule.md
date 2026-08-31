---
type: insight
date: 2026-08-01
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

N150 and C328 establish that gap types carry directional implications (breakaway=chase, exhaustion=fade), while R082 mandates that breakouts must be accompanied by heavy volume to be valid. Combining these: a breakaway gap with heavy volume satisfies R082's validity condition and should be chased, whereas a gap occurring on light or declining volume — particularly after an extended trend — is more likely an exhaustion gap and should be faded. The volume signature thus becomes the primary discriminator between gap types that are otherwise ambiguous at the moment of formation.

## Trading Implication

When a gap forms, immediately check volume: heavy volume on a gap following a consolidation signals a valid breakaway gap to enter with trend; thin volume on a gap after an extended move signals an exhaustion gap to fade or exit existing positions.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related
- [[EN008-volume-confirmation-at-pattern-completion]] — See EN008-volume-confirmation-at-pattern-completion for the foundational volume rule that underpins the gap-type chase/fade discriminator
