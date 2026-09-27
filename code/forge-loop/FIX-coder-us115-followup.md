# US-115 Follow-up: STR-B Exit Model Fix + CSV entry_type

**Date:** 2026-08-16
**Agent:** Coder
**Task:** Fix two issues flagged by risk guardian

---

## Issue 1 — STR-B Exit Model Misalignment (VETOED)

### Problem
STR-B used `_simulate_exit` (close-only checks, fills at close price) while all
other 9 scanners used `_walk_forward_exit` (intrabar high/low checks, fills at
exact stop/target price). This caused 28.4% of STR-B trades to have gap-through
stops with R < -1 (worst: -8.585R). Results were not comparable across scanners.

### Changes Made

**File:** `scripts/validation/scanners/scanner_b_macd_divergence.py`

1. **Replaced `_simulate_exit` with `_walk_forward_exit`**
   - Copied the standard implementation from scanner_x/scanner_z
   - Walks forward bar-by-bar from `entry_idx + 1`
   - Checks `low[j] <= stop_price` (longs) / `high[j] >= stop_price` (shorts)
   - Stop exits fill at `stop_price`, R = -1.0 (capped, no gap-through)
   - Target exits fill at `target_price`, R computed dynamically
   - Time stop at MAX_HOLD_BARS, exits at close

2. **Refactored `scan()` to standard pattern**
   - Removed exit simulation from `scan()` — signal dicts no longer contain
     exit_price/exit_reason/r_multiple/bars_held
   - Signal dicts now include `signal_type` field ('macd_bear_div' / 'macd_bull_div')

3. **Added `run_backtest()` function**
   - Standard pattern matching all other scanners
   - Calls `scan()` then `_walk_forward_exit()` per signal
   - Returns trade dicts with exit_type/exit_price/bars_held/r_multiple/signal_type/entry_type

4. **Added `run_phase1a()` function**
   - Multi-ticker wrapper, matching other scanners' interface

5. **Increased MAX_HOLD_BARS from 8 to 15**
   - Renamed `MAX_BARS_HELD` to `MAX_HOLD_BARS` (consistent with other scanners)
   - Aligned with STR-Z and STR-AA (both use 15)

6. **Updated `__main__` smoke test**
   - Now uses `run_backtest()` instead of `scan()`
   - Verifies no R < -1 on stop exits

**File:** `scripts/validation/run_phase1a_v3_us115.py`

7. **Replaced `run_backtest_b` adapter with direct import**
   - Removed the 30-line adapter that wrapped `scan()` and mapped fields
   - Now imports `run_backtest as bt_b` directly (like all other scanners)
   - Updated `SCANNER_MAP` to use `bt_b`

### Verification
- Import: OK
- SPY backtest: 15 trades (15 short, 0 long)
- Stop exits: 12, with R < -1: **0** (all stops exactly -1.0R)
- signal_type: populated ('macd_bear_div')
- entry_type: populated ('pullback' / 'market')

---

## Issue 2 — entry_type Missing from CSV Writer

### Problem
The `market_structure` module computes `entry_type` ('pullback' or 'market')
but the CSV writer's `std_cols` list didn't include it, so the field was dropped
from output CSVs. Cannot verify pullback feature's value-add.

### Changes Made

**File:** `scripts/validation/run_phase1a_v2_us114.py`
- Added `'entry_type'` to both `std_cols` lists (empty DataFrame + result DataFrame)

**File:** `scripts/validation/run_phase1a_v3_us115.py`
- Added `'entry_type'` to both `std_cols` lists (empty DataFrame + result DataFrame)

**File:** `scripts/validation/scanners/scanner_b_macd_divergence.py`
- Added `"entry_type": sig.get("entry_type", "")` to `run_backtest()` trade dict
  so the field is actually populated for STR-B

### Note
Other scanners' `run_backtest()` functions do not yet pass `entry_type` through
to their trade dicts. The CSV column will exist (filled with empty string for
those scanners). STR-B is the first scanner to populate it. Other scanners can
be updated in a future pass without re-running backtests.

---

## Commit
```
b20d8cc US-115: Fix STR-B exit model + add entry_type to CSV writer
4 files changed, 162 insertions(+), 104 deletions(-)
```
