---
id: US-071
epic: EPIC-010
type: story
status: backlog
created: 2026-07-20
points: 3
tags: [paper-trading, reporting, discord]
depends-on: US-066, US-068
---

# US-071: Paper Trading Performance Report

## Story
As the system operator, I want a daily/weekly Discord summary of paper trading activity, so that I can monitor performance without manually inspecting the trade log.

## Acceptance Criteria
- [ ] Script `scripts/paper_trading/performance_report.py` that reads `trades.csv` and produces:
  - Open positions: count, by strategy, aggregate risk % (heat)
  - Closed trades (since last report): count, win rate, avg R, by strategy
  - Best/worst trade since last report
  - Running totals since inception: total trades, win rate, avg R, by strategy and by asset class (stock/crypto)
- [ ] Hermes cron job: daily summary posts to a dedicated Discord channel (recommend new `#paper-trading` channel — flag for user to create, following the same pattern as `#stock-setups`/`#crypto-setups`)
- [ ] Report format matches the evidence-based style already used elsewhere (facts vs. interpretation separated, no editorializing on small sample sizes)

## Definition of Done
- performance_report.py runs against real trade log data
- Cron job created and confirmed via `hermes cron list`
- Committed to main
