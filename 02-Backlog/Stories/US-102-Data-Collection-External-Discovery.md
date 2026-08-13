---
type: user-story
status: done
epic: EPIC-011
priority: high
created: 2026-08-13
completed: 2026-08-13
---

# US-102: Data Collection Phase + External Edge Discovery

## Story
As a trading researcher, I need to collect sufficient trade data across all strategies before implementing portfolio heat management, AND I need ongoing external research to discover new trading edges from web, X, and academic sources.

## Acceptance Criteria

### Part A: Heat Cap Suspension
- [x] `capture_signals.py` heat cap enforcement disabled (logs but does not block)
- [x] All strategies can fire freely to accumulate validation data
- [x] Performance report shows actual heat (not capped at 5%)
- [x] Strategy correlation tracking added to daily performance report

### Part B: External Edge Discovery
- [x] Cron job searches web, X/Twitter, and vault for new trading edges
- [x] Posts findings to #strategy-research channel
- [x] Runs 3x per week (Tue/Thu/Sun 16:00 UTC)
- [x] Proposes actionable, testable hypotheses (not vague concepts)
- [x] Avoids duplicating existing strategies
- [x] Uses free data only (daily OHLCV)

## Rationale
We can't optimize portfolio construction before strategies are validated. Need data collection first. Simultaneously, we need ongoing external research to find new edges — the existing weekly research pipeline is purely quantitative (factor screening from price data) and doesn't search external sources.

## Implementation
- `capture_signals.py`: Removed `continue` on heat limit, now logs warning only
- `performance_report.py`: Added strategy correlation section (overlapping drawdown detection)
- Cron `e214a9d8f348`: External Edge Discovery agent (web + x_search + file toolsets)
