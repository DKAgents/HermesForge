---
id: US-098
epic: EPIC-014
type: story
status: backlog
created: 2026-08-07
points: 1
tags: [backlog, story]
---

# US-098: Hermes Config Set CLI Bug

## Story
**As the** system administrator,
**I want** the hermes config set CLI bug for list-valued keys documented and worked around,
**So that** config changes don't silently corrupt list values.

## Acceptance Criteria
- [ ] Document the bug (#16493): hermes config set corrupts list-valued keys
- [ ] Workaround: use terminal + Python yaml/manual diff instead of hermes config set for list-valued keys
- [ ] Monitor bug fix; when resolved, test and remove workaround note

## Notes / Context
> Affects config.yaml edits for list-valued configuration options. Workaround is reliable.

## Dependencies
- Blocks: None
- Blocked by: None

## Definition of Done
- [ ] Code/config implemented
- [ ] Tests passing (paper mode verified)
- [ ] Risk Guardian reviewed (if applicable)
- [ ] Documented in vault
- [ ] ADR created (if architectural decision)
