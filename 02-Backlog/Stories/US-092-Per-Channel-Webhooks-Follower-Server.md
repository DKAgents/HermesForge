---
id: US-092
epic: EPIC-013
type: story
status: backlog
created: 2026-08-07
points: 2
tags: [backlog, story]
---

# US-092: Per-Channel Webhooks — Follower Server

## Story
**As a** publishing system,
**I want** separate webhooks for #stock-setups, #strategy-status, and #strategy-research in the follower server,
**So that** each channel's content crossposts to the correct follower channel without cross-contamination.

## Acceptance Criteria
- [ ] User creates webhooks in follower server for each channel (#stock-setups, #strategy-status, #strategy-research)
- [ ] Each webhook URL stored as `CROSSPOST_WEBHOOK_{CHANNEL_ID}` in `.env`
- [ ] `webhook_utils.py` already supports per-channel lookup (no code changes needed)
- [ ] Test each channel posts to correct follower channel — no cross-contamination

## Notes / Context
> BLOCKED on user creating webhooks in follower server Discord settings. The code is ready — `webhook_utils.py` already performs per-channel env var lookup. This is purely a configuration step on the Discord side.

## Dependencies
- Blocks: None
- Blocked by: User action (Discord server configuration — creating webhooks in follower server)

## Definition of Done
- [ ] Code/config implemented
- [ ] Tests passing (paper mode verified)
- [ ] Risk Guardian reviewed (if applicable)
- [ ] Documented in vault
- [ ] ADR created (if architectural decision)
