# US-114: STR-AJ Intermarket Caching Fix

**Date:** 2026-08-16
**Scanner:** STR-AJ (Intermarket Rotation)
**File:** `scripts/validation/scanners/scanner_aj_intermarket.py`
**Commit:** `0ff00a8` — `US-114: Fix STR-AJ intermarket caching — fetch DXY/TNX once, not per ticker`

## Problem

The `scan()` function was recently updated to auto-fetch DXY/TNX data when `intermarket` is `None` (interface compatibility fix). However, the fetch happened **per ticker** — every call to `scan()` triggered a new yfinance download or parquet read.

When scanning 529 stocks:
- 529 redundant DXY/TNX fetches (even with parquet cache, 1,058 file reads + compute_intermarket_signal() x529)
- 529 spam warning prints: `[STR-AJ] No intermarket data — auto-fetching DXY/TNX...`
- Extremely slow batch scans

## Fix

Added a module-level cache `_INTERMARKET_CACHE` that stores the computed intermarket signal DataFrame after the first fetch.

### Changes

1. **Module-level cache variable:**
   ```python
   _INTERMARKET_CACHE = None
   ```

2. **Cache-aware `scan()` logic:**
   - When `intermarket` is `None` or empty:
     - Check `_INTERMARKET_CACHE` — if populated, use it (no fetch, no print)
     - If `None`, fetch DXY/TNX once via `fetch_intermarket_data()`, compute signal via `compute_intermarket_signal()`, store in `_INTERMARKET_CACHE`
   - The "auto-fetching" print only appears on the first call (inside the `else` block), not on cached calls

3. **Cache clearing function:**
   ```python
   def clear_intermarket_cache():
       global _INTERMARKET_CACHE
       _INTERMARKET_CACHE = None
   ```
   Allows callers to force a re-fetch when parquet caches on disk have been updated.

## Testing

### Import test
```
cd scripts/validation/scanners && python -c 'import scanner_aj_intermarket; print("import OK")'
→ import OK
```

### Functional test
- Read SPY.parquet, called `scan(df.tail(100), 'SPY', long_only=True)`
- First call: printed `[STR-AJ] No intermarket data — auto-fetching DXY/TNX (one-time)...`, fetched data, populated cache
- Second call `scan(df.tail(100), 'AAPL', long_only=True)`: NO fetch message, used cache silently
- Verified `_INTERMARKET_CACHE is not None` after first call → True

## Impact

- Batch scans of 529 stocks: DXY/TNX fetched **1 time** instead of **529 times**
- Warning spam eliminated (1 message instead of 529)
- No behavioral change to signal generation — same intermarket DataFrame used for all tickers
- `run_phase1a()` already fetched once and passed via `intermarket=` arg, so its behavior is unchanged (the cache is only exercised when `intermarket=None`)
