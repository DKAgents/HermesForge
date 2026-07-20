---
id: US-067
epic: EPIC-010
type: story
status: done
created: 2026-07-20
points: 5
tags: [paper-trading, position-sizing, risk]
depends-on: US-065
---

# US-067: Position Sizing & Portfolio Heat Enforcement

## Story
As a risk-conscious paper trading system, I need each strategy's own validated position sizing rules applied to every paper trade, and portfolio-level heat/concurrency limits enforced, so that paper trading results are risk-realistic and comparable to how the strategies would actually be sized live.

## Acceptance Criteria
- [ ] Module `scripts/paper_trading/position_sizing.py` with one sizing function per strategy:
  - `size_strategy_b(confirmation_level, weekly_gates_passing) -> risk_pct` — implements the Level x Weekly-gate matrix from the STR-B note (0.25%-1.0%)
  - `size_strategy_a(...) -> risk_pct` — flat 1% (PS-001)
  - `size_strategy_d(...) -> risk_pct` — flat 1% (PS-001)
  - Dispatch function `get_risk_pct(strategy_id, signal_dict) -> float` routes to the right function
- [ ] Portfolio heat check: `check_portfolio_heat(new_risk_pct) -> (allowed: bool, reason: str)`
  - Reject (or flag) if adding the new trade would exceed 5% aggregate open risk (ADR-004)
  - Reject (or flag) if already at 5 concurrent open positions
- [ ] `capture_signals.py` (US-066) updated to call `get_risk_pct()` and `check_portfolio_heat()` before opening a trade; on rejection, log as skipped with reason, do not open the trade
- [ ] Position size formula applied: `size = (account_capital * risk_pct) / abs(entry - stop)` — uses `EXAMPLE_ACCOUNT_SIZE` from `scripts/discord/config.py` for consistency with existing alert sizing display
- [ ] Unit tests: Strategy B Level 2 + all-3-weekly-gates-passing -> 0.5% risk; Level 1 + 2-3-gates-failing -> 0.5% risk (verify matrix lookup matches the STR-B table exactly); Strategy A/D always 1%; portfolio heat correctly rejects a 6th concurrent position

## Definition of Done
- position_sizing.py unit tests pass, matrix values verified against STR-B note's Step 3 table
- capture_signals.py enforces heat/concurrency limits
- Committed to main
