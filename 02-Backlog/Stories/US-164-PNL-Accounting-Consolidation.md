---
type: user-story
epic: EPIC-014
priority: P1
status: backlog
created: 2026-10-31
tags: [pnl-integrity, tech-debt]
---

# US-164 — Consolidate duplicate PNL accounting into one module

## Problem

`hostile_fills.py`, `hostile_fills_strq.py`, and `hostile_fills_strq_v2.py` carry byte-identical accounting functions — `_apply_taker_fee`, `_compute_r`, `_adversarial_cost_drag`, `_paper_r`, `_reconcile_signal_dedup`, `_authoritative_close`, `_close_outcome`. Every future accounting fix must be hand-applied 2–3×. Risk-guardian verdict (round 3): "drift is a matter of when, not if."

## Fix

Extract the shared accounting functions into one module (e.g. `scripts/paper_trading/pnl_accounting.py`) and have all three files import from it. Keep the variant-specific differences as parameters/config — entry-fill semantics (bar-open vs signal-price limit), `ENTRY_MODE`, `REPORT_PATH` — so consolidation is behavior-preserving.

## Acceptance

- All three files import the shared accounting module (no duplicate definitions).
- `py_compile` clean; targeted parity tests confirm identical output to the pre-consolidation behavior (119 quarantine / 20 bps adversarial penalty / zombie exclusion all preserved).
- No behavior change; path-scoped commit.