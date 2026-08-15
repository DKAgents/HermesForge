---
type: user-story
story: US-108
epic: EPIC-013
title: "Tiered Sweep Filter, STR-Q Discord Alerts, and Heatmap Wiring"
status: Done
created: 2026-08-15
completed: 2026-08-15
tags: [sweep, str-q, discord, heatmaps, tiered-filter]
---

# US-108: Tiered Sweep Filter, STR-Q Discord Alerts, and Heatmap Wiring

## Summary

Implements the US-108 work items following the Phase 1B v2 deep walk-forward validation and confluence study. Three immediate fixes and three medium-term studies, all completed in one session.

## Acceptance Criteria

1. ✅ Tiered sweep filter — STR-D uses require mode, STR-A/B/I use boost mode
2. ✅ Equal_lows excluded on stocks (34.6% WR in deep backtest)
3. ✅ STR-Q alerts posted to #stock-setups and #crypto-setups on trade open
4. ✅ Heatmaps regenerated and posted to Discord channels
5. ✅ post_heatmaps.py import bug fixed (REPO_ROOT path)
6. ✅ US-108 backlog story created

## Implementation Details

### 1. Tiered Sweep Filter (`sweep_timing_filter.py`)
- Added `TIERED_MODES` dict mapping strategy prefixes to modes
- Added `_get_mode_for_strategy()` function
- `check_sweep_alignment()` now accepts `strategy_id` parameter
- Mode is automatically selected based on strategy:
  - STR-D → require (weakest baseline, strongest sweep fit)
  - STR-A/B/I → boost (already have internal confirmation)
- `capture_signals.py` passes `strategy_id` to the filter

### 2. Equal_lows Stock Exclusion (`sweep_timing_filter.py`)
- Added `EXCLUDED_STOCK_LEVEL_TYPES = {"equal_lows"}`
- Added `_filter_valid_sweeps()` function that filters by:
  - Quality score ≥ MIN_SWEEP_QUALITY
  - Confirmation status
  - Asset-type exclusions (equal_lows on stocks)
  - Premium level types filter (optional, for future use)
- Applied in both `check_sweep_alignment()` and `capture_sweep_signals.py`

### 3. STR-Q Discord Alerts (`capture_sweep_signals.py`)
- Added `_post_str_q_alert()` function
- Posts rich embed to #crypto-setups (1528555885310513213) or #stock-setups (1528555538848153640)
- Embed includes: entry/stop/target, R:R, sweep details (penetration, wick, volume), level type, confluence explanation
- Day-of-week color coding matching existing embed_publisher convention
- Called after every successful trade open

### 4. Heatmap Wiring Fix (`post_heatmaps.py`)
- Fixed `REPO_ROOT` path bug: was `parent.parent` (scripts/), changed to `parent.parent.parent` (HermesForge root)
- Added `scripts/discord` to sys.path
- Heatmaps verified posting to:
  - #daily-market-briefing (correlation + sector rotation)
  - #strategy-research (all 4, weekly)
  - #paper-trading (strategy-regime, performance report)

## Files Modified

| File | Changes |
|------|---------|
| `scripts/data/sweep_timing_filter.py` | Added TIERED_MODES, _get_mode_for_strategy, _filter_valid_sweeps, strategy_id param, sweep_level_type in returns |
| `scripts/paper_trading/capture_signals.py` | Pass strategy_id to sweep filter, sweep_level_type field |
| `scripts/paper_trading/capture_sweep_signals.py` | Import _filter_valid_sweeps, apply equal_lows filter, _post_str_q_alert function, call alert on trade open |
| `scripts/discord/post_heatmaps.py` | Fixed REPO_ROOT path bug |

## Validation

- Tiered filter logic tested: STR-D→require, STR-A/B/I→boost, STR-Q→boost (default)
- Equal_lows filter tested: excluded on stocks, kept on crypto
- STR-Q dry-run capture: no errors, runs clean
- Heatmap posting: verified live to 3 Discord channels
