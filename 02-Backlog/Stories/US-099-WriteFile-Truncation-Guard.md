---
id: US-099
epic: EPIC-014
type: story
status: backlog
created: 2026-08-07
points: 1
tags: [backlog, story]
---

# US-099: WriteFile Truncation Guard

## Story
**As the** development system,
**I want** a guard against write_file silently truncating very long content,
**So that** large files are not partially written without warning.

## Acceptance Criteria
- [ ] Document the issue: write_file can silently truncate content exceeding a threshold in a single call
- [ ] Workaround documented: write first section via write_file, then patch(mode=replace) to append each subsequent section
- [ ] Consider a length-verification step after write_file (compare bytes_written to expected content length)

## Notes / Context
> Workaround is reliable. Low frequency but high impact when it triggers (partial files).

## Dependencies
- Blocks: None
- Blocked by: None

## Definition of Done
- [ ] Code/config implemented
- [ ] Tests passing (paper mode verified)
- [ ] Risk Guardian reviewed (if applicable)
- [ ] Documented in vault
- [ ] ADR created (if architectural decision)
