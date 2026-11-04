---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-03
owner: architect
tags: [reporting, r-accounting, fill-realism, gauntlet]
---

# US-223 — Rewire performance report to lead with fill-realistic R

## Problem

The paper-trading performance report leads with OPTIMISTIC R (`gauntlet_r` =
`gross_r − fee_drag`, no bar-level fill-timing correction), printing
`+3734R / +0.93 R/trade`. US-169 (`7fe4518e`) claimed to "drop the optimistic
breakdown" but the report still leads with it. The honest bar-level `hostile_r`
is (a) not in `trades.csv` (no column), (b) surfaced only as a buried
STR-Q-only line, and (c) degraded to 59 trades (−12R) because the bar history
was purged (US-189). See
`reports/performance-report-old-R-findings-2026-11-03.md`.

## Fix

1. Rewire `scripts/paper_trading/performance_report.py` to LEAD with the
   fill-realistic (bar-level hostile) R; demote `gauntlet_r` (cost-adjusted but
   close-fill) to a clearly-labeled secondary line ("not fill-realistic").
2. Document that the pre-purge bar-level history is unrecoverable (US-189);
   surface the CURRENT bar-level R honestly, labeled with its coverage window.
3. Fail-closed guard: the report must NEVER present an un-fill-realistic R as
   the headline — if the fill-realistic R is unavailable, say so explicitly
   rather than silently falling back to the optimistic number.

## Acceptance Criteria

- Report headline = fill-realistic R (bar-level where available), never the
  optimistic `gauntlet_r` alone.
- The optimistic number, if shown at all, is labeled "not fill-realistic."
- A test asserts the report refuses/annotates an un-fill-realistic headline.

## Owner / RACI
- Owner (A): architect · Responsible (R): coder · Consulted (C): risk-guardian · Informed (I): orchestrator