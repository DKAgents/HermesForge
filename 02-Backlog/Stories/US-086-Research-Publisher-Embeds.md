---
id: US-086
epic: EPIC-013
type: story
status: done
created: 2026-08-06
points: 5
tags: [backlog, story]
---

# US-086: Research Publisher Embeds

## Story
**As a** research communication system,
**I want** research findings published as rich Discord embeds with day-colored borders and layman narratives,
**So that** non-technical readers can understand what the pipeline found.

## Acceptance Criteria
- [x] `research_publisher.py` built
- [x] 3-embed split to respect Discord 6000-char total limit
- [x] Day-of-week colored borders applied to embeds
- [x] Layman narrative dictionaries created for each factor/strategy
- [x] Deletes old messages before posting new results
- [x] Crossposts to follower server

## Notes / Context
> Commits 9942c6f and 67c2734. The publisher bridges the gap between raw pipeline output and human-readable Discord communication, using narrative dictionaries to translate technical metrics into accessible language.

## Dependencies
- Blocks: None
- Blocked by: US-085 (pipeline must produce output to publish)

## Definition of Done
- [x] Code/config implemented
- [x] Tests passing (paper mode verified)
- [x] Risk Guardian reviewed (if applicable)
- [x] Documented in vault
- [x] ADR created (if architectural decision)
