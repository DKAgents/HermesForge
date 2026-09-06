---
id: US-135
epic: EPIC-014
type: story
status: ready
created: 2026-09-06
priority: P3
tags: [backlog, story, robustness, snapshot, incident-log]
campaign: 2026-09-aegis-rebuild
train: 0
owner_profile: coder
model_floor: T3
points: 1
depends_on: US-134
---

# US-135 — Add incident log to snapshot payload

## Story

As the operator, I need the incident log preserved in snapshots so that the
incident history at the time of each snapshot is recoverable.

## Background

US-129 investigation found: `07-Risk/INCIDENT_LOG.md` and
`07-Risk/GUARDIAN_DECISIONS.md` are NOT purged (safe on disk) but are also NOT
included in snapshot payloads. If the vault were lost, the incident history
would be unrecoverable.

## Acceptance

- [ ] Add `07-Risk/INCIDENT_LOG.md` to snapshot payload
- [ ] Add `07-Risk/GUARDIAN_DECISIONS.md` to snapshot payload
- [ ] Snapshot JSON metadata records: `incident_log_bytes`,
      `guardian_decisions_bytes`
- [ ] No compression needed (these are small text files, <5 KB each)

## Forbidden

- No publisher file edits
- No cron create/update/remove
- No credentials in output