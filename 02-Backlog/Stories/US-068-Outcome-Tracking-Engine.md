---
id: US-068
epic: EPIC-010
type: story
status: backlog
created: 2026-07-20
points: 5
tags: [paper-trading, outcome-tracking, stocks]
depends-on: US-065, US-066
---

# US-068: Outcome Tracking Engine (Stocks, Intraday High/Low)

## Story
As a paper trading system, I need a daily job that checks every open stock trade against fresh OHLC data — using intraday high/low (not just close) — so that stop and target hits are detected realistically, including wicks that a close-only check would miss.

## Acceptance Criteria
- [ ] Script `scripts/paper_trading/track_outcomes.py` that:
  1. Loads all open trades from `trade_log.py`
  2. For each open trade, fetches the latest cached bar(s) since entry_date for that ticker
  3. For each bar (in chronological order, oldest-unchecked-first): checks in this priority order —
     - Target hit: `high >= target_price` (long) or `low <= target_price` (short)
     - Stop hit: `low <= stop_price` (long) or `high >= stop_price` (short)
     - If both target and stop conditions are true on the same bar (gap-through scenario), use the strategy's documented tie-break rule where one exists (e.g. STR-A's gap-through stop rule), otherwise default to **stop wins** (conservative)
     - Time stop: bars_held >= strategy's max_bars_held (varies: 8 for B, 12 for A, 8 for D — pull from each strategy's Exit Criteria)
  4. On any hit: calls `trade_log.close_trade()` with exit_date, exit_price (target_price/stop_price on hit day, or close price on time-stop), exit_reason
  5. Trades with none of the above still open — left as-is
- [ ] Handles multi-day gaps between checks (e.g. weekend, missed run) by walking all unchecked bars in sequence, not just the latest one
- [ ] Prints summary: N open before, N closed (by reason breakdown), N still open
- [ ] Unit test with synthetic OHLC data: verify a long trade closes on target when high crosses target_price even though close < target_price (the core "wick" case this story exists for)

## Definition of Done
- track_outcomes.py unit test passes for the wick-detection case
- Runs against real cached SPY/strategy-B trade data without errors
- Committed to main
