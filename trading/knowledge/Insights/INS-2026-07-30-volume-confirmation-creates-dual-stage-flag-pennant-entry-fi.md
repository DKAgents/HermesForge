---
type: insight
date: 2026-07-30
actionability: 4
connection_type: creates_filter
domains: [indicators, patterns, rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume Confirmation Creates Dual-Stage Flag/Pennant Entry Filter

## Discovery Summary

N043 establishes that flags/pennants resume on a 'burst of trading activity' after a light-volume consolidation phase. R082 generalizes this: all pattern breakouts require heavy volume to be valid. N013 adds a specific false-breakout detection rule: a light-volume breakout followed by heavy-volume decline is a confirmed trap. Together, these three notes create a two-stage volume filter specifically for flag/pennant breakouts — first confirming the consolidation volume dried up properly, then confirming the breakout volume surges meaningfully.

## Trading Implication

A trader should only enter a flag/pennant breakout if (1) volume visibly contracted during the 1-3 week consolidation and (2) breakout volume surges above the consolidation average; if the breakout occurs on light volume, treat it as a potential bull trap and wait for a subsequent heavy-volume decline to confirm exit or avoidance.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**creates_filter** — Actionability score: 4/5

## Related
- [[R002-dow-averages-must-confirm-each-other]] — See R002-dow-averages-must-confirm-each-other for the parallel principle of requiring dual confirmation before acting on signals

- [[EN008-volume-confirmation-at-pattern-completion]] — See EN008-volume-confirmation-at-pattern-completion for the foundational Murphy rule that underlies this filter
