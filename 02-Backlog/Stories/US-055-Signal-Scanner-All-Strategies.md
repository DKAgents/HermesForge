---
id: US-055
epic: EPIC-007
type: story
status: backlog
created: 2026-07-20
points: 8
tags: [validation, scanner, phase1a, strategies]
depends-on: US-054
---

# US-055: Signal Scanner — All Four Strategies

## Story
As a strategy validator, I need a signal scanner for each of the four swing strategies so that I can measure signal frequency and rough outcome distributions on historical data.

## Acceptance Criteria
- [ ] One scanner module per strategy in `scripts/validation/scanners/`
- [ ] Each scanner ingests the cached OHLCV data from US-054
- [ ] Each scanner outputs a CSV: one row per triggered setup with fields defined below
- [ ] All discretionary rules operationalized — every rule produces a yes/no from OHLCV data
- [ ] Outcome estimation: for each setup, compute outcome at (a) primary target, (b) stop, (c) 8-bar time stop — whichever hits first
- [ ] R-multiple computed for each setup: (outcome price − entry) / (entry − stop)
- [ ] Sub-period label attached to each row
- [ ] Summary report printed per strategy: signal count/year, avg R, median R, win rate, sub-period breakdown
- [ ] Results saved to `scripts/validation/results/STR-XXX-phase1a.csv`

## Output CSV Schema (per setup row)
```
ticker, date, entry_price, stop_price, target_price, exit_price, exit_reason,
r_multiple, bars_held, sub_period, strategy_id,
[strategy-specific tag fields per Open Questions]
```

## Strategy-Specific Operationalization

### Strategy A — MA Pullback + Fibonacci
- 50-day MA rising: slope > 0 over last 5 bars
- Price within 38–62% Fibonacci retracement of prior advance (highest high to lowest low in prior 40 bars)
- Entry trigger: RSI crosses above 40 from below (RSI[0] > 40 AND RSI[1] <= 40)
- Stop: close below 62% Fibonacci level
- Target: prior swing high (highest high in prior 40 bars)
- Weekly filter (soft): price above 200-day MA as proxy for weekly trend
- Tag fields: fib_entry_zone (38/50/between), trigger_type (rsi_cross), ma_slope

### Strategy B — MACD Histogram Divergence
- Maturity gate: MACD line continuously above zero for 15+ bars (bearish) or below zero (bullish)
- Stage 1: histogram narrowing — abs(hist[0]) < abs(hist[1]) for 2+ consecutive bars, both above zero (bearish)
- Stage 2: price makes new 10-bar high while MACD line makes lower high vs. prior comparable swing
- Level 2 confirmation: RSI >= 70 (bearish) or <= 30 (bullish)
- Entry trigger: MACD line crosses below signal line
- Stop: 0.5 * ATR(14) above divergence swing high
- Target: nearest prior swing low below entry (lowest low in prior 20 bars)
- Tag fields: confirmation_level (1/2), macd_bars_above_zero, weekly_gates_passing (0-3)

### Strategy C — Breakout + Volume
- Price breaks above 20-bar high (close > max(high[-20:-1]))
- Volume on breakout bar > 1.5x 20-day avg volume
- Stop: low of breakout bar
- Target: breakout height projected upward (breakout level + (breakout level - prior base low))
- Tag fields: volume_ratio, breakout_bar_range

### Strategy D — S/R Role Reversal
- Prior resistance level identified: highest high in bars -60 to -20
- Price pulls back to that level (within 1%)
- Entry trigger: close above the level after touching it
- Stop: 1 ATR below the level
- Target: next resistance level above (highest high in prior 100 bars, above current level)
- Tag fields: level_age_bars, touch_depth_pct

## Technical Notes
- Pandas-based; no event-driven framework needed for Phase 1A
- Long-only for A, C, D; both directions for B
- frictionless (no commission/slippage)
- Survivorship bias acknowledged — document in output header

## Definition of Done
- 4 scanner modules runnable independently
- Results CSVs generated for all 4 strategies
- Summary report shows signal count/year, avg R, sub-period breakdown
- Committed to main
