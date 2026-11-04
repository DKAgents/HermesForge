---
type: user-story
epic: EPIC-017
priority: P2
status: backlog
created: 2026-11-03
owner: coder
tags: [r-accounting, data-integrity, dedup, hostile-fill]
---

# US-225 — Stage-authoritative hostile jsonls (prune stale skip rows)

## Problem

The hostile-fill jsonls dedup on `(signal_id, stage)` as a deliberate "transition
trail," so a signal_id can accumulate BOTH a `stage:"skip"` row (from an early
cron run when 5m bars were missing/out-of-window) AND a `stage:"closed"` row
(from a later run once bars were available). The stale skip row is never pruned
— a data-gap artifact masquerading as a terminal "hostile never entered"
verdict. See `reports/hostile-r-duplicate-keys-and-persistence-findings-2026-11-03.md`.

## Fix

Make the jsonl **stage-authoritative**: a later `open_entry`/`closed` stage for a
given signal_id (STR-Q) / trade_id (swing) SUPERSEDES an earlier `skip` stage.
Concretely:

1. On write, when a trade resolves to a non-skip stage, drop/overwrite any prior
   `skip` row for that identity (a data-gap skip is not a terminal verdict — it
   is re-scored once bars exist).
2. Keep the legitimate `open_entry -> closed` transition (an open trade later
   closing) — a `closed` supersedes an `open_entry`.
3. Do NOT change the READ-side resolution (US-223 already reads "closed, non-null
   hostile_r, latest wins").

## Acceptance Criteria

- Running the generator twice (first with bars unavailable → skip, then with bars
  available → closed) leaves ONE authoritative row per signal_id (the closed),
  not a growing trail.
- A genuine "no fill even with bars available" skip is still recorded as skip.
- Existing jsonls are pruned once (idempotent) so the current stale skip rows are
  removed.

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): risk-guardian · Informed (I): orchestrator