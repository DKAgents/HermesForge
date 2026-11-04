---
type: user-story
epic: EPIC-017
priority: P2
status: backlog
created: 2026-11-03
owner: coder
tags: [r-accounting, fill-realism, degenerate-stop, hostile-fill, swing]
---

# US-227 — Add degenerate-stop/outlier gate to swing hostile model

## Problem

The swing hostile model (`scripts/paper_trading/hostile_fills.py`) does not
compute/emit `outlier_excluded` or apply a DEGENERATE_RISK_FLOOR gate, whereas
STR-Q (`hostile_fills_strq.py`) does. A near-zero-risk swing stop (setup risk <
`DEGENERATE_RISK_FLOOR`) therefore produces a meaningless/fabricated `hostile_r`
instead of being marked unscoreable. The read-side guard and US-224 backfill
already honor `outlier_excluded` — but no swing row carries it, so swing closes
are never degenerate-stop-protected. Harmless today (0 swing outliers), but a
latent scope gap the STR-Q path already closes.

## Fix

1. In `hostile_fills.py` (swing), compute setup risk (`|entry − widened_stop| /
   entry`) and mark `outlier_excluded: True` when below `pnl_accounting.
   DEGENERATE_RISK_FLOOR`, matching STR-Q's behavior exactly.
2. Emit `outlier_excluded` on every swing record so the read-side guard + US-224
   backfill honor it (never treat a degenerate-stop hostile_r as a real R).
3. Re-run the swing generator to populate the field on existing swing rows
   (expected 0 outliers today, but the field must exist and be consistent).

## Acceptance Criteria

- Swing hostile records carry `outlier_excluded`; the degenerate-stop gate
  behaves identically to STR-Q.
- A near-zero-risk swing trade is marked outlier_excluded (not scored as a real
  R), never a fabricated value.
- Tests pass; existing swing R values are unchanged (0 outliers today).

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): risk-guardian · Informed (I): orchestrator