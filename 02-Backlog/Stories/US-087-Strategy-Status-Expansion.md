---
id: US-087
epic: EPIC-013
type: story
status: done
created: 2026-08-06
points: 3
tags: [backlog, story]
---

# US-087: Strategy Status Expansion

## Story
**As a** strategy dashboard,
**I want** to display both manual and research pipeline strategies in a unified view,
**So that** all 24 strategies are visible in one place.

## Acceptance Criteria
- [x] `strategy_status.py` updated to include research pipeline strategies
- [x] 2 groups displayed: Manual (16) + Research Pipeline (8)
- [x] CANDIDATE emoji/color applied to research pipeline entries
- [x] Deletes ALL previous messages before reposting
- [x] Field splitting implemented for fields exceeding 1024 chars
- [x] Crossposts to follower server

## Notes / Context
> Unified dashboard gives a single-pane view of all deployed and candidate strategies, distinguishing manual from research-pipeline-sourced entries via the CANDIDATE designation.

## Dependencies
- Blocks: None
- Blocked by: US-088 (webhook crossposting for follower server delivery)

## Definition of Done
- [x] Code/config implemented
- [x] Tests passing (paper mode verified)
- [x] Risk Guardian reviewed (if applicable)
- [x] Documented in vault
- [x] ADR created (if architectural decision)
