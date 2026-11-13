---
type: insight
date: 2026-11-12
actionability: 4
connection_type: adds_condition
domains: [concepts, patterns, rules]
sources: ["N150-price-gaps-types", "R082-breakouts-must-be-accompanied-by-heavy-volume", "C328-gaps"]
seed_id: gap_continuation_volume
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume Separates Breakaway Gaps from Common Gaps

## Discovery Summary

N150-price-gaps-types identifies breakaway gaps as trend-start signals, but R082-breakouts-must-be-accompanied-by-heavy-volume adds the condition that pattern breakouts are valid only with heavier volume. Therefore, a gap that looks like a breakaway but lacks a volume surge should not be chased as a true breakout; it is more likely a common gap. For exhaustion gaps, the taxonomy already says to treat them as trend-end signals, so fading them is appropriate, while any subsequent opposite breakaway leg should also satisfy the R082 volume test.

## Trading Implication

Before trading a gap, check volume: enter in the gap direction only if it is a breakaway gap confirmed by heavy volume; otherwise ignore it as a common gap, and treat exhaustion gaps as exit/fade signals.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**adds_condition** — Actionability score: 4/5
