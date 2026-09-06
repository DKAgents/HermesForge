---
id: US-134
epic: EPIC-014
type: story
status: ready
created: 2026-09-06
priority: P2
tags: [backlog, story, robustness, snapshot, cron-evidence, forensic]
campaign: 2026-09-aegis-rebuild
train: 0
owner_profile: coder
model_floor: T3
points: 2
depends_on: US-133
---

# US-134 — Add cron output and maintenance logs to snapshot payload

## Story

As the operator, I need cron execution evidence preserved in the snapshot
archive so that post-incident forensics can access diagnostic context even
after the on-disk retention window expires.

## Background

US-129 investigation found: snapshots protect journal + CSV + crosspost_state
but do NOT include cron output or maintenance logs. After 35 days, ALL
diagnostic context is gone. Adding these to the snapshot payload closes the
gap permanently — even a 35-day-old snapshot includes the cron output from
that window.

## Acceptance

- [ ] `snapshot_restore.py` snapshot payload expanded to include:
      - `~/.hermes/cron/output/` (compressed as `cron_output.tar.gz`)
      - `04-ForgeLoop/Maintenance/` (compressed as `maintenance_logs.tar.gz`)
- [ ] Snapshot JSON metadata records: `cron_output_bytes`, `cron_output_sha256`,
      `maintenance_logs_bytes`, `maintenance_logs_sha256`
- [ ] Weekly restore drill verifies the compressed payloads are valid
- [ ] Snapshot directory size estimate after change: ~290 KB → ~3.5 MB
- [ ] No impact on snapshot speed (compression adds <5s)

## Forbidden

- No publisher file edits
- No cron create/update/remove
- No credentials in output