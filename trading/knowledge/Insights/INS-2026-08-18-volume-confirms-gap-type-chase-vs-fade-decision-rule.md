---
type: insight
date: 2026-08-18
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

N150 and C328 distinguish gap types by their trend implications (breakaway=new trend, runaway=trend continuation, exhaustion=trend end), but neither provides a validation mechanism. R082 supplies that mechanism: volume confirmation at breakouts. Combining these, a breakaway gap with heavy volume is a chase signal (trend initiation confirmed), a runaway gap with sustained volume confirms trend continuation, while an exhaustion gap — particularly one with declining volume or followed by a counter-gap (island reversal per N150) — is a fade signal.

## Trading Implication

On any gap open, immediately check volume relative to recent average: a breakaway or runaway gap with volume surge above the 20-day average warrants trend-following entry, while a gap with flat or declining volume — especially after a prolonged trend — should be treated as a potential exhaustion gap and faded with a tight stop above the gap high.

## Supporting Notes

- [[N150-price-gaps-types]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[C328-gaps]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related Notes
- [[R003-volume-confirms-the-trend|Volume Confirms the Trend]]
