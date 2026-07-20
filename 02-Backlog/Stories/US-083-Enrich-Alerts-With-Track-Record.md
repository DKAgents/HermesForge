---
id: US-083
epic: EPIC-013
type: story
status: backlog
created: 2026-07-20
points: 3
tags: [closed-loop, discord, alerts]
depends-on: EPIC-010
---

# US-083: Enrich Discord Alerts with Live Track Record

## Story
As a Discord alert recipient, I want to see the issuing strategy's recent real track record alongside each new signal, so that I can weigh the alert with actual performance context, not just the backtested tier.

## Acceptance Criteria
- [ ] `alert_publisher.py` (from US-064) extended with a "Recent Track Record" line: e.g. "Last 10 signals: 60% win rate, avg R 0.8"
- [ ] Pulled from `trades.csv` closed trades for that strategy_id
- [ ] Gracefully omits this line if fewer than 5 closed trades exist yet (avoid misleading small-sample claims)

## Definition of Done
- Alert format updated and smoke-tested with both sufficient and insufficient sample-size cases
- Committed to main

## Dependencies
Blocked until EPIC-010 produces enough closed trades to be meaningful.
