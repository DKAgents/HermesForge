---
id: US-082
epic: EPIC-013
type: story
status: backlog
created: 2026-07-20
points: 3
tags: [closed-loop, quality-tier]
depends-on: EPIC-010
---

# US-082: Quality-Tier Calibration

## Story
As the system operator, I want to know whether Tier A alerts actually outperform Tier B alerts in real paper trading outcomes, so that the quality-tier logic (added in US-064) is evidence-based rather than assumed.

## Acceptance Criteria
- [ ] Analysis script comparing closed paper trade R-multiples grouped by quality tier at signal time
- [ ] Report states finding with explicit confidence level and sample size (per user's evidence-based analysis preference — no claims beyond what sample size supports)
- [ ] If Tier A does not outperform Tier B with reasonable confidence, flag the tier logic (US-064) for revision

## Definition of Done
- Tier calibration report produced with real data
- Recommendation made (keep as-is / revise) with explicit reasoning
- Committed to main

## Dependencies
Blocked until EPIC-010 has enough closed trades to distinguish tiers statistically.
