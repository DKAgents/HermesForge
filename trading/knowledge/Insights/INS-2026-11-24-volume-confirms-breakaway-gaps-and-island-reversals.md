---
type: insight
date: 2026-11-24
actionability: 4
connection_type: creates_filter
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume confirms breakaway gaps and island reversals

## Discovery Summary

N150-price-gaps-types says breakaway gaps signal the start of a new trend, while R082-breakouts-must-be-accompanied-by-heavy-volume says a breakout is real only if heavier trading activity accompanies it. Therefore a gap that appears to be a breakaway should be traded as one only with a volume surge; otherwise it is more likely a common gap and should be ignored or faded. C328-gaps' claim that up/down gaps indicate strength/weakness is thus conditional on volume confirmation. This also gives a sequence for island reversals: the first exhaustion gap ends the old trend, but the confirming opposite breakaway gap must show heavy volume.

## Trading Implication

Require a volume expansion to classify any gap as a breakaway; do not chase gaps that lack volume confirmation. For island reversals, wait for the opposite breakaway gap on heavy volume before fading the prior trend.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5
