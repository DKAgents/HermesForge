---
id: EPIC-013
type: epic
status: backlog
created: 2026-07-20
updated: 2026-07-20
tags: [epic, closed-loop, self-improvement, quality-tier]
---

# EPIC-013: Closed-Loop Improvements

## Goal

Feed real paper trade outcomes back into strategy evaluation and alert quality scoring, closing the loop between "signal generated" and "did it actually work." Depends on EPIC-010 producing a meaningful volume of closed paper trades first.

## Stories

| Story | Title | Status |
|---|---|---|
| US-081 | Feed Paper P&L into Phase 1B/1C Strategy Classification | ⬜ Backlog |
| US-082 | Quality-Tier Calibration (does Tier A actually outperform Tier B?) | ⬜ Backlog |
| US-083 | Enrich Discord Alerts with Live Track Record | ⬜ Backlog |
| US-084 | Wire Outcome Data into Pending-Updates Mechanism | ⬜ Backlog |

## Definition of Done
- Strategy classification (kill/watch/pass) incorporates live paper outcomes alongside backtested Phase 1A/1B results
- Quality tier logic (A/B/High/Medium) validated or adjusted based on real outcome data
- Discord alerts show recent track record for the issuing strategy
- Contradicting live results trigger a Pending-Updates entry per the existing US-052/053 mechanism

## Dependencies
- Blocked by EPIC-010 (needs closed paper trades to have real data to feed back)
