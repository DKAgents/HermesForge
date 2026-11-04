---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-03
owner: coder
tags: [data-integrity, dedup, double-count, trades.csv]
---

# US-226 — Dedup trades.csv duplicate signal_id rows at source

## Problem

`trades.csv` carries ~19 duplicate `signal_id` rows (the known `_write_all_rows`
dup bug, documented in `performance_report.py._dedupe_rows`). US-224 gave those
duplicates a real `hostile_r`, activating a latent double-count: summing
`trades.csv.hostile_r` WITHOUT dedup = −45.01R (124 rows) vs −25.63R (105
identities) = a ~19.4R over-statement. Currently contained only by consumers
that dedup first — a read-time patch over a root-cause defect.

## Fix

1. Root-cause + fix the `_write_all_rows` duplicate bug (or the journal →
   trades.csv projection) so duplicate signal_id rows can no longer be written.
2. One-time dedup of the existing `trades.csv` — remove duplicate signal_id rows,
   keeping the authoritative (latest/closed) row; never drop unique rows.
3. A guard so `trades.csv` is append-unique by signal_id going forward.

## Acceptance Criteria

- `trades.csv` has zero duplicate signal_id rows after the fix (12,514 → fewer,
  but every unique identity preserved).
- Summing `hostile_r` with no dedup equals the deduped sum (105 identities,
  −25.63R) — no consumer can double-count.
- The write bug is fixed at the source, not just re-deduped on read.

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): risk-guardian · Informed (I): orchestrator