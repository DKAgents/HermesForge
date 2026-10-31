---
type: insight
date: 2026-10-25
actionability: 3
connection_type: confirms_risk_rule
domains: [indicators, patterns, rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Volume divergence flags false breakout, tighten stops

## Discovery Summary

The volume divergence during a trend (e.g., declining volume on new highs) often precedes a false breakout from continuation patterns like flags or pennants (N043). Rule R082 mandates heavy volume on breakouts, and indicator N013 uses volume as a filter for false breakouts. Thus, when volume diverges from price within a flag/pennant, it confirms the risk rule and signals a likely false breakout, advising stop tightening.

## Trading Implication

During a flag or pennant breakout, if volume is decreasing relative to the prior trend, treat the breakout as suspect and tighten stop-losses or exit partially.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**confirms_risk_rule** — Actionability score: 3/5
