---
id: US-057
epic: EPIC-007
type: story
status: backlog
created: 2026-07-20
points: 3
tags: [validation, paper-trading, phase1c, infrastructure]
---

# US-057: Paper Trade Log Infrastructure (Phase 1C)

## Story
As a strategy validator, I need a structured paper trade log so that I can record live and Bar Replay paper trades in a format that answers the Open Questions and feeds the self-improvement loop.

## Acceptance Criteria
- [ ] CSV trade log template created at `scripts/validation/paper_trades.csv` with schema below
- [ ] Obsidian template created at `Templates/Paper-Trade-Template.md` for per-trade reflection notes
- [ ] Log ingestion script: `scripts/validation/log_trade.py` — adds a row to CSV from CLI args
- [ ] Analysis script: `scripts/validation/analyze_paper_trades.py` — reads CSV, produces per-strategy summary
- [ ] Compatible with `extract_lessons.py` (self-improvement loop input)
- [ ] Per-strategy Open Question fields captured in CSV schema
- [ ] Risk envelope enforced in log_trade.py: warns if new trade would exceed 5% portfolio heat
- [ ] README documents how to log a trade after a TradingView Bar Replay session

## CSV Schema
```
trade_id, strategy_id, ticker, direction (long/short),
entry_date, entry_price, stop_price, target_price,
exit_date, exit_price, exit_reason (target/stop/time/invalidation),
r_multiple, bars_held, sub_period,
confirmation_level, weekly_gates_passing,
trigger_type, notes
```

## Definition of Done
- log_trade.py accepts CLI args and appends to CSV
- analyze_paper_trades.py produces per-strategy summary with R stats
- Templates committed to vault
- Committed to main
