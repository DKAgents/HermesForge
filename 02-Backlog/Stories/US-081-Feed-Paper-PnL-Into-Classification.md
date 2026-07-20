---
id: US-081
epic: EPIC-013
type: story
status: backlog
created: 2026-07-20
points: 5
tags: [closed-loop, strategy-classification]
depends-on: EPIC-010
---

# US-081: Feed Paper P&L into Phase 1B/1C Strategy Classification

## Story
As a strategy validator, I want live paper trading outcomes to supplement the backtested Phase 1A/1B classification, so that kill/watch/pass decisions reflect real forward performance, not just historical scanner results.

## Acceptance Criteria
- [ ] Extend `run_phase1a.py`'s classification logic (or a new script) to also ingest `trades.csv` paper trade outcomes for each strategy
- [ ] Report shows backtested avg R alongside live paper avg R, side by side
- [ ] Flag any strategy where live results diverge meaningfully from backtested expectations (threshold TBD — start with a simple >0.3 R difference flag)

## Definition of Done
- Combined backtest+live report generated for at least one strategy with real paper trade history
- Committed to main

## Dependencies
Blocked until EPIC-010 has produced enough closed paper trades to be meaningful (recommend waiting for at least 10-15 closed trades per strategy before treating this data as informative).
