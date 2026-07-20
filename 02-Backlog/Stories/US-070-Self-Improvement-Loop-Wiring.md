---
id: US-070
epic: EPIC-010
type: story
status: backlog
created: 2026-07-20
points: 3
tags: [paper-trading, self-improvement, lessons]
depends-on: US-068
---

# US-070: Self-Improvement Loop Wiring

## Story
As a systematic trader, I want every closed paper trade to automatically feed the existing lesson-extraction pipeline (US-053), so that the vault's knowledge base learns from real paper trading outcomes without manual triggering.

## Acceptance Criteria
- [ ] `track_outcomes.py` (US-068), on closing a trade, calls `extract_lessons.py` (or the equivalent US-053 mechanism) with the closed trade's full context as input
- [ ] Confirm `extract_lessons.py` actually exists and is callable — if it was only specified in US-053's acceptance criteria but never built, this story includes building the minimal version needed to accept paper-trade input (do not assume it exists; verify first)
- [ ] Lesson notes generated reference the originating trade_id and strategy_id
- [ ] If a closed trade's outcome contradicts the strategy's expected edge (e.g. Strategy B closes at stop when Tier A should mean high confidence), flag for Pending-Updates per the existing US-052/053 mechanism
- [ ] Test: manually close a synthetic trade, verify a lesson note is written to `09-Journal/Lessons/`

## Definition of Done
- Closed trades produce lesson notes automatically
- Pending-Updates flagging works for at least one contradicting-outcome test case
- Committed to main
