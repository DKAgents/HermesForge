---
id: US-097
epic: EPIC-014
type: story
status: backlog
created: 2026-08-07
points: 2
tags: [backlog, story]
---

# US-097: Headroom Retrieve Bug

## Story
**As the** system administrator,
**I want** the headroom_retrieve bug tracked and worked around permanently,
**So that** proxy retrieval doesn't silently fail and cause missing context.

## Acceptance Criteria
- [ ] Document the upstream bug (headroom GitHub issue #1077, fix PR #1323 merged for Responses API path, PR #1176 still unmerged for chat-completions path)
- [ ] Workaround: redirect-to-file + search_files/read_file pattern instead of trusting retrieval (documented in headroom-proxy-management skill)
- [ ] Monitor PR #1176 merge status; when merged, test retrieval and remove workaround

## Notes / Context
> Confirmed upstream bug. Root cause and diagnostic recipe in headroom-proxy-management skill references.

## Dependencies
- Blocks: None
- Blocked by: None

## Definition of Done
- [ ] Code/config implemented
- [ ] Tests passing (paper mode verified)
- [ ] Risk Guardian reviewed (if applicable)
- [ ] Documented in vault
- [ ] ADR created (if architectural decision)
