# US-114 Coder Batch 3 — STR-R + STR-AJ Fixes

**Date:** 2026-08-16
**Scanner:** STR-R (Alligator), STR-AJ (Intermarket)
**Audit ref:** US-114 swarm audit (3-agent)

---

## STR-R: scanner_r_alligator.py — 4 bugs fixed

### Bug 1 (CRITICAL) — Sleep exit hardcoded r_multiple=0
**Location:** `_walk_forward_exit()`, lines ~248-259
**Before:**
```python
if last["alligator_sleeping"]:
    exit_price = df.iloc[i]["close"]
    return {"exit_type": "sleep", "exit_price": exit_price,
            "bars_held": i - entry_idx, "r_multiple": 0}  # simplified
```
**After:**
```python
if last["alligator_sleeping"]:
    exit_price = df.iloc[i]["close"]
    risk = abs(entry_price - stop_price)
    if risk > 0:
        if direction == "long":
            r_multiple = (exit_price - entry_price) / risk
        else:
            r_multiple = (entry_price - exit_price) / risk
    else:
        r_multiple = 0
    return {"exit_type": "sleep", "exit_price": exit_price,
            "bars_held": i - entry_idx, "r_multiple": round(r_multiple, 3)}
```
**Impact:** Sleep exits were always recorded as R=0 regardless of P&L. This contaminated all backtest statistics (win rate, avg R, profit factor). Verified fix: SPY backtest now shows sleep exits with real R values (-0.045, 0.032).

### Bug 2 (PERFORMANCE) — O(n^2) recomputation of compute_alligator
**Location:** `_walk_forward_exit()`, lines ~249-250
**Before:**
```python
for i in range(entry_idx + 1, min(entry_idx + max_bars + 1, n)):
    r = compute_alligator(df.iloc[:i+1])  # recomputes ALL bars 0..i each iteration
    ...
    last = r.iloc[-1]
```
**After:**
```python
alligator_data = compute_alligator(df)  # compute ONCE
for i in range(entry_idx + 1, min(entry_idx + max_bars + 1, n)):
    last = alligator_data.iloc[i]  # index into precomputed data
```
**Impact:** Each bar in the holding window triggered a full recomputation of the Alligator indicator from bar 0 to bar i. With 20 bars in the window and ~1000+ bars of data, this was O(n * max_bars * n) per trade. Now O(n) per trade. Results are mathematically identical (SMMA with adjust=False is recursive; value at i depends only on data 0..i).

### Bug 3 (FRAGILE) — Date field used fragile fallback expression
**Location:** `scan()`, lines 176 and 201 (long and short signal dicts)
**Before:**
```python
"date": row.name if hasattr(row.name, 'strftime') else str(row.get("date", i)),
```
**After:**
```python
"date": result.index[i],
```
**Impact:** The `row.get("date", i)` fallback could produce integer indices instead of dates when the index wasn't datetime. Using `result.index[i]` directly is clean, consistent with other scanners, and always returns the correct index value.

### Bug 4 — Entry-end check required full MAX_HOLD_BARS window
**Location:** `run_backtest()`, line 292
**Before:**
```python
if entry_idx + MAX_HOLD_BARS >= len(df):
    continue
```
**After:**
```python
if entry_idx + 1 >= len(df):
    continue
```
**Impact:** Trades in the last 20 bars of data were silently skipped. Other scanners only require at least 1 bar after entry. Fixed to match the standard contract — `_walk_forward_exit` already handles the case where fewer than `max_bars` bars remain.

---

## STR-AJ: scanner_aj_intermarket.py — Interface fix

### Interface incompatibility — 4th required parameter
**Location:** `scan()` function signature, line 173
**Before:**
```python
def scan(df, ticker, long_only=False, intermarket=None) -> list:
    if intermarket is None or len(intermarket) == 0:
        return []  # immediately returns empty when called with 3 args
```
**After:**
```python
def scan(df, ticker, long_only=False, intermarket=None) -> list:
    if intermarket is None or len(intermarket) == 0:
        print("    [STR-AJ] No intermarket data — auto-fetching DXY/TNX...", flush=True)
        im_data = fetch_intermarket_data()
        if im_data.get("DXY") is None or im_data.get("TNX") is None:
            print(f"    [STR-AJ] WARNING: Could not fetch intermarket data for {ticker} — skipping")
            return []
        intermarket = compute_intermarket_signal(im_data["DXY"], im_data["TNX"])
        if intermarket is None or len(intermarket) == 0:
            print(f"    [STR-AJ] WARNING: Insufficient DXY/TNX overlap — skipping {ticker}")
            return []
```
**Impact:** When called with the standard 3-arg contract `scan(df, ticker, long_only)` — as the swarm orchestrator and other callers do — STR-AJ immediately returned `[]` because `intermarket` was `None`. Now it auto-fetches DXY/TNX via the existing `fetch_intermarket_data()` + `compute_intermarket_signal()` pipeline. If fetch fails, it prints a warning and returns `[]` gracefully. Verified: 3-arg call on SPY produced 34 signals.

---

## Verification

```
$ python -c 'import scanner_r_alligator; import scanner_aj_intermarket; print("Both import OK")'
Both import OK

STR-R: 34 trades on SPY
  Sleep exits: 2
  Sleep exit R=-0.045 (should NOT be hardcoded 0)
  Sleep exit R=0.032 (should NOT be hardcoded 0)

STR-AJ 3-arg call: 34 signals (auto-fetch path works)
```

## Commit
```
US-114 coder: Fix STR-R bugs (R=0 sleep, O(n^2), date) + STR-AJ interface
```
