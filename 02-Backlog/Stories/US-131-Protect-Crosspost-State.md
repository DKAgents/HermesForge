---
id: US-131
epic: EPIC-014
type: story
status: story-ready
created: 2026-09-06
tags: [backlog, story, robustness, publisher, crosspost-state, p1]
campaign: 2026-09-aegis-rebuild
train: 0
priority: P1
owner_profile: publisher
model_floor: T2
---

# US-131 — Protect crosspost_state.json (guard + snapshot class)

- **Train:** 0
- **Priority:** P1
- **Owner profile:** publisher
- **Model floor:** T2
- **Status:** story-ready
- **Campaign:** 2026-09-aegis-rebuild

## Story

As the publisher, I need `crosspost_state.json` protected to the same class as
trade history — write guards plus inclusion in the snapshot regime — so that a
corrupt or truncated state file cannot cause duplicate or dropped cross-posts and
cannot be silently lost.

## Background

Evidence from campaign `2026-09-aegis-rebuild`:

- Invariants require the "same protection class for `crosspost_state.json`" as
  trades.
- `data-manifest.md` does not record `crosspost_state_bytes`; no guard is
  described. State size/integrity is UNVERIFIED.
- `crosspost_state.json` is publisher-owned. Aegis does not touch it; publisher
  implements the guard.

## Acceptance

- [ ] Writes to `crosspost_state.json` go through an atomic temp→fsync→rename
      path; refuse empty payload and refuse regression (e.g. fewer posted IDs
      than before without an explicit reset).
- [ ] `crosspost_state.json` is included in the US-126 snapshot regime (on-box
      ≥35d + off-box), and `crosspost_state_bytes` is recorded in the data
      manifest.
- [ ] Test specified: simulate an interrupted write; assert the previous valid
      state survives and no duplicate/dropped posts result.
- [ ] Rollback specified.

## Forbidden

- No live-soul edits
- Only publisher may edit publishing code / `crosspost_state.json`
- No truncate/replace of the state file — guard is atomic and additive
- No credentials or webhook URLs in repo or output

## Rollback

Feature-flag the guarded write path; revert to the current write on regression.
State file is small and snapshotted, so recovery is a snapshot restore.
