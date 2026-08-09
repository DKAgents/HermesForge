---
id: US-088
epic: EPIC-013
type: story
status: done
created: 2026-08-06
points: 5
tags: [backlog, story]
---

# US-088: Webhook Crossposting System

## Story
**As a** publishing system,
**I want** webhook-based crossposting to follower server channels,
**So that** messages can be deleted without leaving tombstones.

## Acceptance Criteria
- [x] `webhook_utils.py` built with `WebhookCrossposter` class
- [x] Posts via webhook URL
- [x] Deletes via webhook token (no tombstone left behind, unlike native crosspost deletion)
- [x] Integrated into `embed_publisher.py`, `strategy_status.py`, `research_publisher.py`
- [x] Tested: message ID 1534849327703261234 posted and successfully deleted (HTTP 204)

## Notes / Context
> Commits 9d7ce4a and af4c7f8. Native Discord crossposts leave tombstones when deleted; webhook-based crossposting avoids this by posting directly to the follower channel via its own webhook, so deletion is clean.

## Dependencies
- Blocks: US-087, US-086 (depend on crossposting integration)
- Blocked by: None

## Definition of Done
- [x] Code/config implemented
- [x] Tests passing (paper mode verified)
- [x] Risk Guardian reviewed (if applicable)
- [x] Documented in vault
- [x] ADR created (if architectural decision)
