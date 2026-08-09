---
id: US-090
epic: EPIC-013
type: story
status: done
created: 2026-08-07
points: 3
tags: [backlog, story]
---

# US-090: LinkedIn Cron Style Refinement

## Story
**As a** content automation system,
**I want** the LinkedIn post generator to match Dan's writing style based on rewrite analysis,
**So that** generated posts sound like a trusted advisor rather than a journalist.

## Acceptance Criteria
- [x] 3 rounds of rewrite analysis completed
- [x] 24 style rules embedded in cron `98a07007974b`
- [x] Em-dashes removed from the prompt itself (root cause of model mimicking them)
- [x] Topic category rotation enforced (no back-to-back same category)
- [x] No setup phrases in generated output
- [x] Narrative storytelling with named tools
- [x] Inline definitions, multi-layer metaphors, strong declarative close
- [x] 300-500+ words minimum enforced

## Notes / Context
> The key discovery was that em-dashes in the system prompt caused the model to mimic them in output — removing them from the prompt itself fixed the style bleed. Rewrite analysis iteratively compared generated posts against Dan's actual writing to extract and codify stylistic patterns.

## Dependencies
- Blocks: None
- Blocked by: None

## Definition of Done
- [x] Code/config implemented
- [x] Tests passing (paper mode verified)
- [x] Risk Guardian reviewed (if applicable)
- [x] Documented in vault
- [x] ADR created (if architectural decision)
