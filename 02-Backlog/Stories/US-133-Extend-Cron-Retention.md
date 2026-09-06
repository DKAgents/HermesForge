---
id: US-133
epic: EPIC-014
type: story
status: ready
created: 2026-09-06
priority: P1
tags: [backlog, story, robustness, retention, cron-evidence]
campaign: 2026-09-aegis-rebuild
train: 0
owner_profile: coder
model_floor: T3
points: 1
depends_on: US-129
---

# US-133 — Extend cron output retention to ≥35 days

## Story

As the operator, I need cron execution evidence retained for at least 35 days
so that post-incident forensics can access diagnostic context for the full
snapshot horizon.

## Background

US-129 investigation found: `maintain_vault.py` purges `~/.hermes/cron/output/`
at **14 days** (line 392: `14 * 86400`). The US-126 snapshot horizon is **35
days**. This creates a 21-day gap where cron evidence is destroyed while
snapshots still exist — but snapshots don't include cron output.

## Acceptance

- [ ] Change 14-day constant to 35 days in `maintain_vault.py:392`
- [ ] Use the same constant or reference `RETENTION_DAYS` from
      `snapshot_restore.py` to keep them in sync
- [ ] Verify: files older than 35 days get purged, files 14-35 days survive
- [ ] Record in data-manifest.md that cron output retention is now 35d
- [ ] No other maintenance behavior changed

## Forbidden

- No publisher file edits
- No cron create/update/remove
- No credentials in output