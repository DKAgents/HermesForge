---
id: US-080
epic: EPIC-012
type: story
status: backlog
created: 2026-07-20
points: 2
tags: [alpaca, scheduling, market-hours]
depends-on: US-078
---

# US-080: Market-Hours Scheduling

## Story
As the execution system, I need stock order placement to respect market hours (9:30 AM-4:00 PM ET), so that no orders are attempted when the market is closed.

## Acceptance Criteria
- [ ] Scheduling logic checks current time against market hours (including early closes/holidays if feasible; at minimum, weekday 9:30-4:00 ET)
- [ ] Cron job for stock execution only fires within this window
- [ ] Signals generated outside market hours queue for the next open rather than being dropped

## Definition of Done
- Market-hours check tested for both in-window and out-of-window cases
- Committed to main
