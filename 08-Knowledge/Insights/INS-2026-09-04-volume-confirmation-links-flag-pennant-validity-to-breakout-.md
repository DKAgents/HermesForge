---
type: insight
date: 2026-09-04
actionability: 4
connection_type: confirms_risk_rule
domains: [indicators, patterns, rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume confirmation links flag/pennant validity to breakout rules

## Discovery Summary

N043 specifies that valid flags and pennants require heavy volume on the breakout to confirm pattern resolution. R082 generalizes this requirement to all price patterns, stating breakouts must show heavier trading activity. N013 further refines this by noting that a light-volume breakout followed by heavy-volume decline is a false signal, creating a specific filter for flag/pennant failures.

## Trading Implication

Only enter flag or pennant breakouts on above-average volume; if the breakout occurs on light volume, tighten stops below the pattern low immediately to avoid being trapped in a false signal.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
