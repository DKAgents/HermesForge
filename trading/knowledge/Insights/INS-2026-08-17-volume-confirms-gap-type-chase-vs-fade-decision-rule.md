---
type: insight
date: 2026-08-17
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
# Volume Confirms Gap Type: Chase vs Fade Decision Rule

## Discovery Summary

N150-price-gaps-types identifies four gap types with opposing directional implications (breakaway=chase, exhaustion=fade), while R082-breakouts-must-be-accompanied-by-heavy-volume establishes that heavy volume is required to validate any breakout signal. Together, these notes create a testable filter: a breakaway gap accompanied by heavy volume is a valid chase signal, while a gap on light or diminishing volume more likely represents an exhaustion gap to fade. C328-gaps confirms that gap direction (up vs down) provides the initial strength/weakness bias, but volume from R082 becomes the discriminating variable between gap types.

## Trading Implication

When a gap occurs, check volume immediately: heavy volume on an up gap after a consolidation suggests a breakaway to chase long; light or declining volume on an up gap after an extended trend suggests an exhaustion gap to fade short. Do not act on gap direction alone without volume confirmation.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
