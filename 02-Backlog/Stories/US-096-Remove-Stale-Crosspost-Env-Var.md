---
id: US-096
epic: EPIC-014
type: story
status: backlog
created: 2026-08-07
points: 1
tags: [backlog, story]
---

# US-096: Remove Stale CROSSPOST_WEBHOOK_URL Env Var

## Story
**As the** system administrator,
**I want** the stale CROSSPOST_WEBHOOK_URL env var removed from the runtime environment,
**So that** it cannot cause confusion or be accidentally re-introduced as a fallback.

## Acceptance Criteria
- [ ] Identify where CROSSPOST_WEBHOOK_URL is being exported/set (not in .env, not in config.yaml, likely from a prior session export)
- [ ] Remove it from wherever it's being set, or add an explicit unset in the Hermes startup sequence
- [ ] Verify: `env | grep CROSSPOST_WEBHOOK_URL` returns nothing after restart

## Notes / Context
> The code no longer reads this var (fixed in US-091), but it still exists in the runtime environment. Harmless but confusing. Low priority.

## Dependencies
- Blocks: None
- Blocked by: None

## Definition of Done
- [ ] Code/config implemented
- [ ] Tests passing (paper mode verified)
- [ ] Risk Guardian reviewed (if applicable)
- [ ] Documented in vault
- [ ] ADR created (if architectural decision)
