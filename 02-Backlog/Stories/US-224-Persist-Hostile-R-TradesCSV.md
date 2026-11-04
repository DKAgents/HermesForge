---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-03
owner: coder
tags: [r-accounting, fill-realism, schema, persistence]
---

# US-224 — Persist authoritative hostile_r onto trades.csv

## Problem

`trades.csv` has no `hostile_r` column (12,514 rows, 0 hostile_r; 7,000 carry the
close-fill cost-adjusted `gauntlet_r`). The bar-level `hostile_r` lives only in
the hostile-fill jsonls, keyed by signal_id/trade_id, so every consumer must
re-join by identity and re-resolve the stage ambiguity (see
`reports/hostile-r-duplicate-keys-and-persistence-findings-2026-11-03.md`).

## Fix

1. Add a `hostile_r` column to `trades.csv` (schema migration, non-destructive —
   existing rows get empty/NULL, never dropped).
2. Backfill `hostile_r` from the AUTHORITATIVE fill-realistic resolution: the
   "closed" stage row with a non-null `hostile_r`; latest timestamp wins where a
   signal_id/trade_id has multiple stages; `outlier_excluded` rows are NOT
   written (or written with an explicit outlier marker, not a false R).
3. Consumers (`performance_report.py` and any other R reader) read `hostile_r`
   directly from `trades.csv`, falling back to the jsonls only when the column is
   empty, so the report stops being jsonl-coupled over time.

## Acceptance Criteria

- `trades.csv` gains a `hostile_r` column; backfilled rows match the jsonl's
  authoritative closed-stage values exactly (spot-check signal_ids across both).
- `performance_report.py` resolves fill-realistic R from `trades.csv` first.
- A test: a row with both skip+closed stages resolves to the closed `hostile_r`.

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): risk-guardian · Informed (I): orchestrator