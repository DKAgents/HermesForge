---
id: US-091
epic: EPIC-014
type: story
status: done
created: 2026-08-07
points: 1
tags: [backlog, story]
---

# US-091: Webhook Fallback Bugfix

## Story
**As a** publishing system,
**I want** webhook crossposting to only use per-channel env vars,
**So that** strategy-status posts don't get sent to the crypto-setups follower channel.

## Acceptance Criteria
- [x] Removed global `CROSSPOST_WEBHOOK_URL` fallback from `get_webhook_for_channel()`
- [x] Verified: strategy-status returns None (uses native crosspost)
- [x] Verified: crypto-setups still uses its per-channel webhook

## Notes / Context
> Commit 2949676. Root cause: global `CROSSPOST_WEBHOOK_URL` env var was set at runtime and used as fallback for all channels. Since one webhook maps to one channel, this caused cross-contamination — strategy-status posts were being sent to the crypto-setups follower channel. Fix: remove the global fallback entirely; only per-channel env vars (`CROSSPOST_WEBHOOK_{CHANNEL_ID}`) are honored.

## Dependencies
- Blocks: None
- Blocked by: None

## Definition of Done
- [x] Code/config implemented
- [x] Tests passing (paper mode verified)
- [x] Risk Guardian reviewed (if applicable)
- [x] Documented in vault
- [x] ADR created (if architectural decision)
