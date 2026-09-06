---
id: US-126
epic: EPIC-014
type: story
status: story-ready
created: 2026-09-06
tags: [backlog, story, robustness, snapshots, offbox, restore-drill, p0]
campaign: 2026-09-aegis-rebuild
train: 0
priority: P0
owner_profile: no-agent
model_floor: no-agent
---

# US-126 — On-box snapshots (≥35d) + off-box copy + weekly restore drill

- **Train:** 0
- **Priority:** P0
- **Owner profile:** no-agent
- **Model floor:** no-agent
- **Status:** story-ready
- **Campaign:** 2026-09-aegis-rebuild

## Story

As the operator, I need real data backups — timed on-box snapshots retained ≥35
days, an off-VPS copy, and a weekly drill that actually restores — so that a
future corruption or truncation is recoverable, unlike the Sep 1–5 loss where no
backup covered the window.

## Background

Evidence from campaign `2026-09-aegis-rebuild`:

- `data-manifest.md`: `snapshot_last_ok: none`, `offbox_last_ok: none`,
  `restore_drill_last_ok: none`.
- Today's only "backup" is Daily Git Push `df2caa`. Git stores the CSV as code —
  **git is not a data backup** and did not cover the lost window.
- Ad-hoc `.bak` files exist (`trades.csv.bak`, `.bak2`, `.bak.heatfix`,
  `.bak.1788717923`) — informal, unmanaged, exactly the anti-pattern the
  protocol warns against.

## Acceptance

- [ ] No-agent snapshot job produces timestamped, checksummed snapshots of the
      trade journal (US-123) and `trades.csv`, retained ≥35 days on-box.
- [ ] An off-VPS copy is written on each snapshot to a destination that is NOT
      the same disk and NOT the GitHub code repo. Destination configured via
      env/secret — never hardcoded, never in the repo.
- [ ] A weekly restore drill reconstructs `trades.csv` from the journal (or from
      the latest snapshot), diffs it against live, and reports OK/FAIL. It writes
      `restore_drill_last_ok` into the data manifest.
- [ ] The ad-hoc `.bak*` files are inventoried and superseded by the managed
      snapshot regime (they are NOT deleted by this story — historical evidence;
      catalog them).
- [ ] Git stores manifests only (`sha256`, rows, `last_id`), not the live data
      file as the backup mechanism.
- [ ] Restore drill IS the test. First successful drill date recorded.
- [ ] Rollback specified.

## Forbidden

- No live-soul edits
- No publisher-file edits unless owner is publisher
- No truncate/replace of history files — snapshots are read-only copies; the
  drill restores to a scratch path, never over live data
- No credentials, off-box destination secrets, or webhook URLs in repo or output

## Rollback

Snapshot + drill jobs are additive and read-only against live data. Disable the
jobs to roll back; nothing depends on them yet. Off-box destination secret is
revocable independently.
