# US-114 Coder Batch 1 — Look-Ahead Bias Fix (STR-S, STR-T, STR-U)

**Date:** 2026-08-16
**Author:** Coder agent (HermesForge swarm, US-114)
**Audit ref:** US-114 swarm audit — 3 scanners flagged for look-ahead bias via `scipy.signal.find_peaks(distance=N)` entry at `pivot_idx + 1`.

## Root cause

`find_peaks(distance=N)` requires **N future bars** to confirm a pivot. Entering at `pivot_idx + 1` therefore uses data that would not yet be available when the pivot is first detectable — the backtest sees the pivot "as known" the bar after it forms, but in reality the pivot is only confirmable `N` bars later. This contaminates the backtest with future information and inflates win rate / R-multiple.

## Fix

For each affected scanner, the entry search start offset was changed from `pivot_idx + 1` to `pivot_idx + PIVOT_DISTANCE`, ensuring the pivot is confirmed before any entry decision is evaluated. The search window end was also de-magic-numbered into a named `ENTRY_SEARCH_WINDOW = 15` constant (value unchanged from the previous literal `15`).

## Per-file changes

### 1. scanner_s_elliott_wave.py (STR-S, PIVOT_DISTANCE = 3)

- **Added constant** `ENTRY_SEARCH_WINDOW = 15` after `PIVOT_DISTANCE` (line ~36).
- **Bullish path (ABC-long entry):**
  - Before (line 135): `for j in range(c_idx + 1, min(c_idx + 15, n)):`
  - After  (line ~137): `for j in range(c_idx + PIVOT_DISTANCE, min(c_idx + ENTRY_SEARCH_WINDOW, n)):`
  - Added explanatory NOTE comment.
- **Bearish path (ABC-short entry):**
  - Before (line 188): `for j in range(c_idx + 1, min(c_idx + 15, n)):`
  - After  (line ~190): `for j in range(c_idx + PIVOT_DISTANCE, min(c_idx + ENTRY_SEARCH_WINDOW, n)):`
  - Added explanatory NOTE comment.

### 2. scanner_t_head_shoulders.py (STR-T, PIVOT_DISTANCE = 5)

- **Added constant** `ENTRY_SEARCH_WINDOW = 15` after `PIVOT_DISTANCE` (line ~38).
- **Regular H&S (short entry):**
  - Before (line 117): `for j in range(R_idx + 1, min(R_idx + 15, n)):`
  - After  (line ~119): `for j in range(R_idx + PIVOT_DISTANCE, min(R_idx + ENTRY_SEARCH_WINDOW, n)):`
  - Added explanatory NOTE comment.
- **Inverse H&S (long entry):**
  - Before (line 157): `for j in range(R_idx + 1, min(R_idx + 15, n)):`
  - After  (line ~159): `for j in range(R_idx + PIVOT_DISTANCE, min(R_idx + ENTRY_SEARCH_WINDOW, n)):`
  - Added explanatory NOTE comment.

### 3. scanner_u_double_top_bottom.py (STR-U, PIVOT_DISTANCE = 4)

- **Added constant** `ENTRY_SEARCH_WINDOW = 15` after `PIVOT_DISTANCE` (line ~34).
- **Double Top (short entry):**
  - Before (line 103): `for j in range(p2_idx + 1, min(p2_idx + 15, n)):`
  - After  (line ~105): `for j in range(p2_idx + PIVOT_DISTANCE, min(p2_idx + ENTRY_SEARCH_WINDOW, n)):`
  - Added explanatory NOTE comment.
- **Double Bottom (long entry):**
  - Before (line 134): `for j in range(t2_idx + 1, min(t2_idx + 15, n)):`
  - After  (line ~136): `for j in range(t2_idx + PIVOT_DISTANCE, min(t2_idx + ENTRY_SEARCH_WINDOW, n)):`
  - Added explanatory NOTE comment.

## Verification

- `python -c 'import scanner_s_elliott_wave; import scanner_t_head_shoulders; import scanner_u_double_top_bottom; print("All 3 import OK")'` → `All 3 import OK`
- Grep for residual `+ 15` magic numbers across the three files → 0 matches.
- Lint (syntax check) passed on every edited file.

## Commit

`US-114 coder: Fix look-ahead bias in STR-S, STR-T, STR-U (entry offset = PIVOT_DISTANCE)`

## Note for next stage

These scanners should now be re-run through walk-forward validation. Per the US-114 audit finding, walk-forward alone was insufficient to catch these biases — the code audit precedes statistical validation. Expect win rates and average R to drop versus the contaminated runs, since entries now occur 3–5 bars later and some patterns will no longer find a confirming close inside the (now shorter) effective search window.
