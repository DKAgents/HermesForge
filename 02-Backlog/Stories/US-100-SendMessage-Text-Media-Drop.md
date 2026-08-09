---
id: US-100
epic: EPIC-014
type: story
status: backlog
created: 2026-08-07
points: 1
tags: [backlog, story]
---

# US-100: SendMessage Text+Media Drop

## Story
**As the** messaging system,
**I want** text and media attachments to be sent reliably in a single message,
**So that** context text is not dropped when attaching files.

## Acceptance Criteria
- [ ] Document the issue: send_message drops the text content when MEDIA:<path> is included in the same message
- [ ] Workaround documented: send text and media as separate messages
- [ ] Monitor for upstream fix; when resolved, test combined send and remove workaround

## Notes / Context
> Affects Discord message delivery. Workaround is simple (two sends) but easy to forget.

## Dependencies
- Blocks: None
- Blocked by: None

## Definition of Done
- [ ] Code/config implemented
- [ ] Tests passing (paper mode verified)
- [ ] Risk Guardian reviewed (if applicable)
- [ ] Documented in vault
- [ ] ADR created (if architectural decision)
