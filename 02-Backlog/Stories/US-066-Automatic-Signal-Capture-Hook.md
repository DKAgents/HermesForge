---
id: US-066
epic: EPIC-010
type: story
status: backlog
created: 2026-07-20
points: 3
tags: [paper-trading, automation, signal-capture]
depends-on: US-065
---

# US-066: Automatic Signal Capture Hook

## Story
As a paper trading system, I want every qualifying signal from the daily scanners to automatically open a paper trade with zero manual entry, so that paper trading coverage matches signal coverage exactly.

## Acceptance Criteria
- [ ] New script `scripts/paper_trading/capture_signals.py` that:
  1. Runs scanners for strategies A, B, D (not just `publish_enabled: true` ones — paper trading has its own gate, independent of Discord publishing)
  2. For each fresh signal (same recency-guard logic as `daily_publish.py`), checks `has_open_trade(strategy_id, ticker)` — skip if already open (max 1 rule)
  3. Computes position size per US-067 (dependency — stub with flat 1% until US-067 lands, then wire in)
  4. Calls `trade_log.open_trade()` with full signal context (chart_path optional at this stage — reuse `chart_generator.py` if convenient, but not blocking)
  5. Prints summary: N signals found, N opened, N skipped (already open), N errors
- [ ] Shares scanner-running logic with `daily_publish.py` where possible (avoid duplicating the scan loop — consider extracting a common helper if the duplication becomes significant)
- [ ] Dry-run mode: `--dry-run` shows what would be opened without writing to trades.csv
- [ ] Smoke test: run against cached SPY data, verify at least one trade would be captured in dry-run

## Definition of Done
- capture_signals.py runs end-to-end against real cached data in dry-run
- No duplicate open trades created for the same (strategy, ticker) pair
- Committed to main
