---
id: US-094
epic: EPIC-014
type: story
status: backlog
created: 2026-08-07
points: 1
tags: [backlog, story]
---

# US-094: Programmatic Em-Dash Filter

## Story
**As the** content publishing pipeline,
**I want** a programmatic regex filter that strips em-dashes from LinkedIn posts before they are sent to Discord,
**So that** the zero-em-dash rule is enforced mechanically rather than relying on LLM self-policing.

## Acceptance Criteria
- [ ] A Python function that scans text for em-dash characters (U+2014, U+2013) and replaces them with regular hyphens, commas, or parentheses
- [ ] Integrated into the LinkedIn cron posting step (either as a script the cron calls before send_message, or as a wrapper around send_message)
- [ ] Tested: feed a sample post with em-dashes, verify output has none

## Notes / Context
> The cron prompt says "scan for em-dashes" but the LLM (deepseek-v4-flash) has failed to self-police multiple times. Root cause was also em-dashes in the prompt itself (now fixed). A programmatic filter is the reliable solution.

## Dependencies
- Blocks: None
- Blocked by: None

## Definition of Done
- [ ] Code/config implemented
- [ ] Tests passing (paper mode verified)
- [ ] Risk Guardian reviewed (if applicable)
- [ ] Documented in vault
- [ ] ADR created (if architectural decision)
