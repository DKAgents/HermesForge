---
id: US-136
epic: EPIC-014
type: story
status: story-ready
created: 2026-09-07
priority: P1
tags: [backlog, story, robustness, snapshot, offbox, durability]
campaign: 2026-09-aegis-rebuild
train: 0
owner_profile: no-agent
model_floor: no-agent
points: 2
depends_on: US-126
---

# US-136 — Activate the off-box snapshot copy (off-VPS invariant unmet)

- **Train:** 0
- **Priority:** P1
- **Owner profile:** no-agent
- **Model floor:** no-agent
- **Status:** story-ready
- **Campaign:** 2026-09-aegis-rebuild

## Story

As the operator, I need each daily snapshot copied to an off-VPS destination so
that a full VPS loss does not destroy the trade journal, CSV projection, and
crosspost state — the off-VPS copy required by the persist invariant is
currently inert.

## Background

Evidence from campaign `2026-09-aegis-rebuild` (second pass, 2026-09-07 UTC):

- FACT: US-126 shipped the snapshot machinery. `scripts/maintenance/snapshot_restore.py`
  contains `_copy_offsite(snap_dir)` and reads destination from
  `OFFSITE_BACKUP_PATH` (supports `/mnt/backup`, `s3://…`, `scp://host/path`).
- FACT: The off-box logic lives in `scripts/maintenance/snapshot_restore.py`
  (NOT under `scripts/paper_trading/` — a `grep OFFSITE paper_trading/*` returns
  nothing, which is expected): line 152 `dest = os.environ.get("OFFSITE_BACKUP_PATH", "")`,
  line 150 `_copy_offsite(snap_dir)`, line 145 sets `result["offbox_copied"]`.
- FACT: The latest snapshot metadata records **`"offbox_copied": false`**
  (`scripts/paper_trading/snapshots/snapshot-20260907.d/snapshot.json`).
- FACT: `OFFSITE_BACKUP_PATH` is **not set** in the environment (checked env,
  `.bashrc`, `.profile`, and the cron surface — absent).
- FACT: Only on-box snapshots exist (2 daily dirs, `snapshots/`).
- INFERENCE: The Train-0 "off-VPS copy" invariant is therefore code-complete but
  operationally unmet. On-box snapshots do not survive VPS loss — the exact
  failure mode the Sep 6 truncation illustrated at a smaller scale.

This is the single remaining Train-0 durability gap after US-123/125/126 shipped.

## Acceptance

- [ ] `OFFSITE_BACKUP_PATH` set to a real off-VPS destination (mount, S3, or
      scp target). Destination credentials live in `.env` / secret store, never
      in the repo or in cron stdout.
- [ ] Next daily snapshot records `"offbox_copied": true` with a recorded
      destination path digest (not the raw credential-bearing URL).
- [ ] `_copy_offsite` failure is surfaced (non-zero exit / alert), not silently
      swallowed — a failed off-box copy must be visible.
- [ ] `data-manifest.md` field `offbox_last_ok` is written with the UTC
      timestamp of the last successful off-box copy.
- [ ] Restore drill (US-137) can read back at least one off-box snapshot.

## Forbidden

- No live-soul edits
- No publisher-file edits (this is durability infra, not publish code)
- No truncate/replace of history files
- No credentials in repo, story, or cron stdout — destination secrets in `.env` only

## Rollback

Unset `OFFSITE_BACKUP_PATH`; snapshots revert to on-box only (current state).
No data is mutated by enabling the copy — it is additive.
