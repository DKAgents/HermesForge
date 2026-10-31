---
type: user-story
epic: EPIC-014
priority: P1
status: backlog
created: 2026-10-31
tags: [pnl-integrity, execution-realism]
---

# US-168 — Full bar-level hostile-fill re-simulation

## Problem

The reconciled per-strategy table (2026-10-31) ran at the paper/accounting layer. The full bar-level re-simulation (re-drive `check_entry_hostile` / `check_exit_hostile` with the 3-bar STR-Q entry lag, worst-print fills, 10 bps taker both sides) is blocked by the absence of `pyarrow` / `fastparquet` in the resolved venv.

## Fix

- Install `pyarrow` (or `fastparquet`) into the resolved venv (via `resolve_python.sh` target / ensurepip), following Rule 1d.
- Re-run the full hostile-fill simulation over OHLCV bar data for the post-09-14 window.
- Produce the final authoritative per-strategy net-R-after-costs table (STR-Q, STR-A, STR-B, STR-D, STR-DEBASEMENT, STR-VIXC).

## Acceptance

- Full bar-level re-run completes; reconciled total == by-strategy == per-trade sums.
- Final per-strategy table + verdict written; explicitly states whether any strategy shows a positive edge once realistic fills + the dynamic fee (US-165) are both applied.