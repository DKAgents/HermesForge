---
id: US-084
epic: EPIC-013
type: story
status: backlog
created: 2026-07-20
points: 3
tags: [closed-loop, pending-updates, self-improvement]
depends-on: US-070
---

# US-084: Wire Outcome Data into Pending-Updates Mechanism

## Story
As the strategy maintenance system, I want contradicting live paper trade results to automatically create a Pending-Updates entry (the existing US-052/053 mechanism), so that strategies get flagged for human review when reality diverges from the documented thesis.

## Acceptance Criteria
- [ ] Extends US-070's lesson extraction: when a lesson's `outcome` field is `contradicts` or `refines`, create/update the corresponding `06-Strategies/Pending-Updates/` entry (same mechanism already defined in ADR-003/US-052)
- [ ] Test: force a contradicting outcome (synthetic), verify a Pending-Updates note is created and links back to the originating trade

## Definition of Done
- Pending-Updates entries created automatically from contradicting live outcomes
- Committed to main
