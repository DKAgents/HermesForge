---
id: US-095
epic: EPIC-014
type: story
status: done
created: 2026-08-07
points: 2
tags: [backlog, story]
---

# US-095: LinkedIn Topic Uniqueness Guard

## Story
**As the** content automation system,
**I want** a programmatic topic uniqueness check that pulls the last 5 LinkedIn posts from Discord channel history and passes their topics to the cron prompt,
**So that** topic repetition is prevented even when the LLM fails to check manually.

## Acceptance Criteria
- [ ] A script that fetches the last 5 bot messages from channel 1518731579067728003 via Discord API
- [ ] Extracts the topic/angle from each (first 2-3 sentences or hashtag-based categorization)
- [ ] Passes the topic list to the cron prompt as context so the LLM knows what was recently covered
- [ ] Programmatic category detection (duplicate data, digital transformation, data pipelines, etc.) and enforcement of no-back-to-back-same-category rule

## Notes / Context
> Currently the LLM is told to check the last 5 posts but has no programmatic way to do so from within the cron session. This is a reliability gap.

## Dependencies
- Blocks: None
- Blocked by: None

## Definition of Done
- [ ] Code/config implemented
- [ ] Tests passing (paper mode verified)
- [ ] Risk Guardian reviewed (if applicable)
- [ ] Documented in vault
- [ ] ADR created (if architectural decision)
