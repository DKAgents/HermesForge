---
type: user-story
epic: EPIC-014
priority: P1
status: backlog
created: 2026-11-01
tags: [backtest, look-ahead, fill-realism]
---

# US-173 — Fix look-ahead close-entry in discovery backtests

## Problem

Discovery backtests (`run_phase1a.py`, `walk_forward.py`, `walk_forward_us114.py`) fill every signal at `close[signal bar]` — the same look-ahead bug #4 that inflated STR-Q. The earlier "US-114 look-ahead fix" corrected scanner *logic*, not the fill convention. Breakout/continuation signals are priced at their own trigger close, inflating edges.

## Fix

Change the fill convention so a signal is only actionable on the bar AFTER its signal bar (fill at next-open, with the adverse-selection cost it implies), across the discovery backtest framework.

## Acceptance

- Discovery backtests no longer price entries at the signal-bar close; they fill at next-open (or an equivalent realistic convention).
- Documented + cited in the backtest metadata.