---
type: user-story
epic: EPIC-014
priority: P1
status: backlog
created: 2026-11-01
tags: [cost-model, backtest]
---

# US-172 — Fix crypto cost in walk_forward.py (5 bp → 12 bp)

## Problem

`walk_forward.py` `apply_costs()` under-charged crypto at 5 bps round-trip vs the corrected 12 bps (fee_source.py). Every crypto-factor walk-forward promotion (STR-P, STR-DEBASE, STR-CAP-BOTTOM) is therefore thinner than its headline number.

## Fix

Point `walk_forward.py`'s crypto cost at `fee_source.py` (12 bps round trip — 2×4.5 taker + 2.5 slip + 0.5 funding) instead of the hardcoded 5 bps. Keep stock consistent with fee_source as well.

## Acceptance

- `walk_forward.py` charges the corrected venue costs via fee_source (no hardcoded 5 bps).
- A walk-forward re-run reflects the corrected drag.