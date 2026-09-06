---
id: US-123
epic: EPIC-014
type: story
status: story-ready
created: 2026-09-06
tags: [backlog, story, robustness, persist, journal, p0]
campaign: 2026-09-aegis-rebuild
train: 0
priority: P0
owner_profile: coder
model_floor: T2
---

# US-123 — Append-only trade journal; trades.csv becomes a derived projection

- **Train:** 0
- **Priority:** P0
- **Owner profile:** coder
- **Model floor:** T2
- **Status:** story-ready
- **Campaign:** 2026-09-aegis-rebuild

## Story

As the HermesForge paper-trading system, I need an append-only fact journal as
the single source of truth (with `trades.csv` rebuilt from it as a derived
projection) so that no process, crash, or in-tolerance row-drop bug can mutate
trade history in place — closing the truncate-class loss that destroyed Sep 1–5.

## Background

Evidence from campaign `2026-09-aegis-rebuild` (read-only inspection of
`scripts/paper_trading/trade_log.py`):

- `_write_all_rows()` (trade_log.py:59) has a real fuse (temp→fsync→verify→
  atomic rename; refuses >20% shrink and empty overwrite). This is the v1
  mitigation from the invariants — a **fuse, not the target**.
- BUT every close path — `close_trade` (:263), `update_entry_status` (:191),
  `register_discord_info` (:164) — **rewrites the entire file**. `trades.csv` is
  the source of truth, a rewrite-the-world file. A row-dropping bug inside the
  20% tolerance, or a crash between rename steps, still corrupts history.
- No append-only journal exists (SCORECARD B-1/B-2).
- `data-manifest.md`: the truncation on 2026-09-06 lost Sep 1–5; no backup
  covered the window.

Target persist contract (from invariants): append-only journal (JSONL or SQLite
WAL; no DELETE/UPDATE on fact rows); `trades.csv` is a derived projection; git
stores code + manifests only.

## Acceptance

- [ ] New append-only journal (JSONL or SQLite WAL) records every open/close/
      update as an immutable fact row; no DELETE/UPDATE on fact rows.
- [ ] `trades.csv` is regenerated from the journal as a derived projection; it is
      never the source of truth.
- [ ] Guards enforced on write: refuse empty payload; refuse row-count
      regression; refuse backward `signal_id` or timestamp.
- [ ] Existing 175 rows migrated into the journal without loss (row count and
      `sha256` recorded in a manifest before and after).
- [ ] v1 fuse in `_write_all_rows` remains in place until the journal is proven
      in paper trading, then is retired in a follow-up, not this story.
- [ ] Test or restore drill specified: unit test proving (a) a mid-write crash
      leaves the journal intact and the projection rebuildable; (b) a
      row-regression write is refused.
- [ ] Rollback specified.

## Forbidden

- No live-soul edits
- No publisher-file edits (owner is coder, not publisher)
- No truncate/replace of history files — journal is additive; do not edit the
  existing `trades.csv` bytes as part of migration except via the derived
  regeneration path
- No credentials in repo or report output

## Rollback

Journal write path is feature-flagged. If the journal misbehaves, disable the
flag; the existing guarded `_write_all_rows` path continues to operate exactly
as today. The journal file is append-only, so disabling it cannot lose data.
Keep the pre-migration `trades.csv` + manifest (`sha256`, rows) as the recovery
baseline.
