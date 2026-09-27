---
type: insight
date: 2026-08-23
actionability: 3
connection_type: adds_condition
domains: [edge-conditions, indicators, risk-guidelines, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "E020-double-crossover-reduces-whipsaws-vs-single-average", "EN028-10-and-50-day-moving-average-crossover"]
seed_id: diversification_position_limit
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Double Crossover Lag Creates Position Sizing Entry Timing Risk

## Discovery Summary

E020 explicitly states the double crossover method 'lags the market a bit more than a single average,' meaning entries on the 10/50 crossover (N039, EN028) occur after optimal price. When combined with strict 1% position sizing (HermesForge rule referenced in seed), the lag-induced late entry erodes the reward-to-risk ratio on each trade before it begins, since stop placement must account for already-moved price. The seed question's 10-15% per market limit from Murphy becomes relevant here: if multiple 10/50 crossover signals fire across correlated stock positions simultaneously (all lagged entries), the portfolio concentration cap provides a second-order protection that the position sizing rule alone does not fully address.

## Trading Implication

When entering on a 10/50 crossover signal, a trader should widen their reward-to-risk threshold requirement (e.g., require minimum 2:1 rather than standard 1.5:1) to compensate for the confirmed lag described in E020, and enforce Murphy's per-market exposure cap to prevent simultaneous lagged entries compounding portfolio-level timing risk.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[E020-double-crossover-reduces-whipsaws-vs-single-average]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**adds_condition** — Actionability score: 3/5

## Related Notes
- [[INS-2026-08-21-pivot-stop-placement-must-satisfy-both-technical-and-rr-crit|Pivot Stop Placement Must Satisfy Both Technical and RR Criteria]]
