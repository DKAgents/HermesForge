---
type: user-story
epic: EPIC-014
priority: P0
status: backlog
created: 2026-11-01
tags: [pnl-integrity, reporting]
---

# US-169 — Regenerate STR-Q ledger + rewire performance report to corrected accounting

## Problem

US-164..168 fixed the accounting *code*, but the data sources the `#paper-trading` report (cron `cb22b038a6d6` → `performance_report.py`) reads are stale: the `gauntlet_r` column in `trades.csv` (old `cost_adjuster`) and the `hostile_r` values in `hostile_fill_report_strq.jsonl` (old `hostile_fills_strq.py`) still carry pre-fix inflated values. The report still posts +3737 R (Optimistic) / +1447 R (L2 "pessimistic") while the corrected bar-level figure is −8,447 R.

## Fix

Regenerate the ledger with the corrected code (`pnl_accounting.py` + `fee_source.py`), reusing the US-168 v3 bar-level re-simulation results (cache/backtester_fidelity_report_v3.md) rather than a fresh multi-hour re-run where feasible. Rewire `performance_report.py` to read the corrected values and REMOVE the misleading "Optimistic R" line entirely (per the publisher redesign "keep the substance, fix the plumbing").

## Acceptance

- The jsonl ledger (`hostile_fill_report_strq.jsonl`) carries corrected `hostile_r` (entry slippage + look-ahead + dynamic fee charged).
- `performance_report.py` no longer emits "Optimistic R"; its displayed R matches the corrected bar-level reconciliation (~−8,447 R).
- Running the report cron produces honest numbers, not +3737 R.