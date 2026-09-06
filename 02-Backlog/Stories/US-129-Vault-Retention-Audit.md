---
id: US-129
epic: EPIC-014
type: story
status: story-ready
created: 2026-09-06
tags: [backlog, story, robustness, vault-retention, investigation, p1]
campaign: 2026-09-aegis-rebuild
train: 0
priority: P1
owner_profile: product-owner
model_floor: T3
---

# US-129 — Investigate Vault Maintenance retention vs RCA/cron evidence

- **Train:** 0
- **Priority:** P1
- **Owner profile:** product-owner
- **Model floor:** T3
- **Status:** story-ready
- **Campaign:** 2026-09-aegis-rebuild

## Story

As the operator, I need confirmation that the daily Vault Maintenance job does
not purge RCA notes, cron execution evidence, or structured logs before their
retention window, so that post-incident forensics (like the Sep 1–5 loss) are
not silently erased.

## Background

Evidence from campaign `2026-09-aegis-rebuild`:

- Vault Maintenance `9d77b5` runs daily 02:00 (T3).
- Protocol Phase B explicitly warns of "vault maintenance purging RCA/cron
  evidence at 14 days."
- `inventory.yaml` is a stub, so the job's actual writable paths and deletion
  rules are UNVERIFIED. This is an investigation story, not a code change.

## Acceptance

- [ ] Document exactly what Vault Maintenance deletes/archives and its retention
      window, sourced from the job definition and script (read-only).
- [ ] Confirm RCA notes, cron execution records, and structured logs are
      retained at least as long as the snapshot horizon (≥35 days per US-126).
- [ ] If retention is shorter than the snapshot horizon, file a follow-up
      coder/publisher story (as appropriate to ownership) to fix it — do NOT
      change the cron in this investigation.
- [ ] Findings written under `reports/campaigns/2026-09-aegis-rebuild/` or an
      RCA note. No cron edits by Aegis.
- [ ] Test/verification: cite the retention rule from source; no fabrication.
- [ ] Rollback specified (N/A — investigation only; note that).

## Forbidden

- No live-soul edits
- No publisher-file edits unless owner is publisher
- No cron create/update/remove in this session
- No truncate/replace of history files
- No credentials in repo or report output

## Rollback

Investigation only — produces a document. Nothing to roll back. Any fix is a
separate, owned story.
