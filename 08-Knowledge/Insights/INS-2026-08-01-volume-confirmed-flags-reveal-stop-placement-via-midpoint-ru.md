---
type: insight
date: 2026-08-01
actionability: 4
connection_type: adds_condition
domains: [indicators, patterns, rules]
sources: ["N043-flag-and-pennant-summary-characteristics", "R082-breakouts-must-be-accompanied-by-heavy-volume", "N013-volume-as-a-filter-for-false-breakouts"]
seed_id: vol_diverge_stop
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Volume-Confirmed Flags Reveal Stop Placement via Midpoint Rule

## Discovery Summary

N043 states that flags and pennants occur at roughly the midpoint of the total market move and form on very light volume before resuming on heavy volume. R082 requires all pattern breakouts to be accompanied by heavy volume to be valid, while N013 specifies that light-volume breakouts from consolidations are likely false, with a subsequent heavy-volume decline confirming failure. Together, these create a two-stage filter: (1) validate the flag/pennant breakout only on heavy volume surge, and (2) use the measured midpoint rule — if volume diverges from the breakout (light volume), the flagpole's implied target is unreliable, and a stop should be placed just below the flag/pennant boundary rather than assuming the full measured move.

## Trading Implication

On a flag or pennant breakout, enter only if accompanied by a clear volume surge per R082; if volume is light at breakout, treat it as a probable false signal per N013 and either abstain or set a tight stop just below the consolidation boundary, since the midpoint-based price target from N043 cannot be trusted without volume confirmation.

## Supporting Notes

- [[N043-flag-and-pennant-summary-characteristics]]
- [[R082-breakouts-must-be-accompanied-by-heavy-volume]]
- [[N013-volume-as-a-filter-for-false-breakouts]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related
- [[RG003-protective-stop-placement-relative-to-round-numbers]] — Avoid round numbers when placing midpoint stops

- [[RG031-protective-stop-placement-as-an-art]] — Adjust midpoint stops for volatility (see RG031)

- [[RG021-use-of-advance-stop-orders-in-point-and-figure-trading]] — See also advance stop placement in point and figure trading
