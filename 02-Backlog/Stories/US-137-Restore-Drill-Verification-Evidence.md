---
id: US-137
epic: EPIC-014
type: story
status: story-ready
created: 2026-09-07
priority: P1
tags: [backlog, story, robustness, restore-drill, durability, evidence]
campaign: 2026-09-aegis-rebuild
train: 0
owner_profile: no-agent
model_floor: no-agent
points: 1
depends_on: US-126
---

# US-137 — Capture restore-drill evidence and write restore_drill_last_ok

- **Train:** 0
- **Priority:** P1
- **Owner profile:** no-agent
- **Model floor:** no-agent
- **Status:** story-ready
- **Campaign:** 2026-09-aegis-rebuild

## Story

As the operator, I need each weekly restore drill to leave a durable, checkable
success record so that "the journal can rebuild the CSV" is a proven fact on a
known date, not an assumption.

## Background

Evidence from campaign `2026-09-aegis-rebuild` (second pass, 2026-09-07 UTC):

- FACT: The Weekly Restore Drill cron (`dfa4ab05ea77`, no-agent, Sunday 08:00,
  `restore_drill.sh` → `snapshot_restore.py --restore-drill`) exists and is
  enabled.
- FACT: There is **no captured drill run** — `~/.hermes/cron/output/dfa4ab05ea77/`
  does not exist, and `data-manifest.md` shows `restore_drill_last_ok: none`.
- FACT: The daily snapshot cron (`291708a04c39`) *does* leave output
  (`.../291708a04c39/2026-09-07_03-00-03.md`), so the capture path works for
  no-agent jobs — the drill simply has not produced a verifiable run yet
  (2026-09-07 is a Monday; the Sunday drill's evidence trail is unconfirmed).
- INFERENCE: A restore capability that has never been observed to complete is
  not yet a restore *guarantee*. The drill must emit a pass/fail record and
  stamp the manifest.

## Acceptance

- [ ] `snapshot_restore.py --restore-drill` writes a dated result record
      (rebuild CSV from journal → diff against live projection → PASS/FAIL) to a
      known path under the repo (e.g. `scripts/paper_trading/snapshots/drill-log/`).
- [ ] On PASS, `data-manifest.md` `restore_drill_last_ok` is updated with the
      UTC timestamp; on FAIL, it is left unchanged and the run exits non-zero.
- [ ] At least one drill run is observed to PASS and its record committed
      (evidence, not intent).
- [ ] Drill exercises an off-box snapshot once US-136 lands (cross-check).

## Forbidden

- No live-soul edits
- No publisher-file edits
- No truncate/replace of history files (drill rebuilds into a temp dir, never
  overwrites the live journal or CSV)
- No credentials in output

## Rollback

Drill remains read-only; if the evidence-writing step misbehaves, revert to the
prior `restore_drill.sh` (verify-only, no manifest write). No live data touched.
