---
type: insight
date: 2026-10-10
actionability: 3
connection_type: adds_condition
domains: [indicators, patterns, trading rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
---

# Tighten stops on low-volume trend divergence

## Discovery Summary

N043 flag-and-pennant-summary-characteristics describes a continuation pattern, but R082 breakouts-must-be-accompanied-by-heavy-volume conditions its validity on volume confirmation. N013 volume-as-a-filter-for-false-breakouts reinforces that absent volume expansion, the breakout is suspect. Thus, when price trends but volume diverges, the continuation signal is weakened and stops should be tightened rather than left wide.

## Trading Implication

Treat trend continuation as vulnerable if volume fails to expand on the breakout; move stops tighter or exit positions showing this divergence.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**adds_condition** — Actionability score: 3/5
