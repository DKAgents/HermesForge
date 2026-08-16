---
type: user-story
story: US-112
epic: EPIC-013
title: "Live Performance Tracker"
status: Done
created: 2026-08-15
completed: 2026-08-15
tags: [performance, tracking, divergence, feedback-loop]
---

# US-112: Live Performance Tracker

## Summary

Built a live performance feedback loop that compares actual paper trading results against backtest expectations and flags when live performance diverges beyond 1.5 standard deviations.

## What It Tracks

For each strategy (STR-Q, STR-B, STR-I, STR-D, STR-A):
- **Win rate** (actual vs expected, with binomial standard error)
- **Average R** (actual vs expected, with sampling error)
- **Stop-hit rate** (actual vs expected)
- **Trade count** (sufficient data threshold: 15-20 trades)
- **Days silent** (flags if no trades in 7+ days)

## Divergence Detection

- z-score computed for each metric: z = (actual - expected) / standard_error
- Flag if |z| > 1.5 (MEDIUM) or |z| > 2.0 (HIGH)
- Silent strategy flag if no trades in 7+ days
- All flags posted to Discord #paper-trading as rich embed alert

## Backtest Expectations (Ground Truth)

| Strategy | Expected Avg R | Expected WR | Source |
|----------|-------------|------------|--------|
| STR-Q | +0.597 | 46.2% | 696-trade deep backtest |
| STR-B | +0.227 | 40.0% | Phase 1A walk-forward |
| STR-I | +0.15 | 35.0% | Phase 1A walk-forward |
| STR-D | +0.033 | 35.0% | Phase 1B (no edge) |
| STR-A | +0.10 | 35.0% | Phase 1A (killed) |

## Implementation

### `live_performance_tracker.py` (new)
- `generate_report()` — Full comparison report for all strategies
- `post_divergence_alert(report)` — Discord alert when flags exist
- `save_report()` — State persisted to `~/.hermes/market_data/live_performance.json`
- CLI: `--update` (after trade closes), `--alert` (post to Discord), `--json` (machine-readable)

## Current Status (First Run)

**Truthful reality check:**
- 6 total trades, 0 closed, 6 open
- STR-Q: 0 live trades (backtest says should be generating signals every 5 min)
- STR-D: never fired (require-mode sweep filter may be too aggressive)
- STR-A: never fired (killed strategy, expected)
- All strategies: INSUFFICIENT DATA

This is exactly the kind of honest feedback the system needs. The tracker will become meaningful once trades start closing.