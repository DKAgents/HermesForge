---
id: US-130
epic: EPIC-013
type: story
status: story-ready
created: 2026-09-06
tags: [backlog, story, publisher, crosspost, release-adopt, p2]
campaign: 2026-09-aegis-rebuild
train: 5
priority: P2
owner_profile: publisher
model_floor: T2
---

# US-130 — Evaluate crosspost job overlap (356f3c vs 61cccd)

- **Train:** 5
- **Priority:** P2
- **Owner profile:** publisher
- **Model floor:** T2
- **Status:** story-ready
- **Campaign:** 2026-09-aegis-rebuild

## Story

As the publisher (sole owner of publishing code), I need to determine whether
the two crosspost jobs are redundant and whether Hermes now provides native
signed outbound webhooks, so that duplicate fan-out can be collapsed to config —
a net deletion — without breaking any channel.

## Background

Evidence from campaign `2026-09-aegis-rebuild`:

- Two no-agent crosspost crons: Auto-Crosspost Daily Briefing `356f3c`
  (5 13 * * 1-5, `webhook_crosspost.sh`) and Webhook Crosspost All Channels
  `61cccd` (*/5, `crosspost_webhook_all.sh`).
- Both local-deliver; overlap is plausible but UNVERIFIED (inventory.yaml stub).
- Hermes is 5917 commits behind (HERMES-RELEASE-DELTA); native signed webhooks
  may now exist and could delete a script.
- These are publisher-owned files. Only publisher may edit them. Aegis files the
  story; it does not touch the code.

## Acceptance

- [ ] Document what each job posts, to which channels, and whether their outputs
      overlap. Channels by name/ID only — never webhook URLs.
- [ ] Determine (from a `hermes update --plan` receipt / changelog) whether
      native signed webhooks can replace either script.
- [ ] If redundant: propose collapsing to one job or to native config, naming
      exactly what is deleted (net deletion required for a Train-5 adopt).
- [ ] Do NOT sequence ahead of Train 0. Blocked-by: US-124 (inventory), and the
      release-delta plan receipt.
- [ ] Test specified: every channel still receives its intended post after any
      change; no duplicate posts.
- [ ] Rollback specified.

## Forbidden

- No live-soul edits
- No non-publisher edits to publishing code (publisher IS the owner here)
- No truncate/replace of history or `crosspost_state.json`
- No credentials or webhook URLs in repo or output

## Rollback

Keep both scripts until the replacement is proven; feature-flag the collapse.
Revert to two-job fan-out if any channel drops.
