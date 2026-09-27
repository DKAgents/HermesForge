# US-114 Coder Batch 2: Look-Ahead Bias + Data Corruption Fixes

**Date:** 2026-08-16
**Agent:** Coder (T2)
**Ticket:** US-114
**Status:** All fixes applied, imports verified, committed

---

## Summary

The US-114 swarm audit identified look-ahead bias in 3 scanners (STR-V, STR-W, STR-AB, STR-AG) and data corruption (duplicate signals) in STR-W. This batch fixes all 4 scanners.

---

## STR-V — scanner_v_triangles.py (PIVOT_DISTANCE=3)

### Fix 1: Look-ahead bias in pivot selection

**Before (line 100-101):**
```python
shs = [j for j in sh_idx if start <= j <= end]
sls = [j for j in sl_idx if start <= j <= end]
```

**After:**
```python
shs = [j for j in sh_idx if start <= j <= end - PIVOT_DISTANCE]
sls = [j for j in sl_idx if start <= j <= end - PIVOT_DISTANCE]
```

**Rationale:** `find_peaks(distance=N)` requires N future bars to confirm a peak. A pivot at bar `j` where `end - j < PIVOT_DISTANCE` is unconfirmed — the algorithm is using future information that wouldn't be available at bar `end`. By excluding pivots within PIVOT_DISTANCE of the window end, we ensure only confirmed pivots are used for trendline fitting.

### Fix 2: Volume bug — zero signals when no volume column

**Before (line 77):**
```python
vol = df["volume"].values if "volume" in df.columns else np.ones(n)
```

**Before (line 129):**
```python
vol_ok = v >= VOLUME_MULT * av if av > 0 else True
```

**Problem:** When no volume column exists, `vol = np.ones(n)`, so `avg_vol = 1.0`, and `vol_ok = (1.0 >= 1.5 * 1.0) = False` for every bar. This silently kills all signals.

**After (line 77-78):**
```python
has_vol = "volume" in df.columns
vol = df["volume"].values if has_vol else np.ones(n)
```

**After (line 130):**
```python
vol_ok = (v >= VOLUME_MULT * av) if (has_vol and av > 0) else True
```

**Rationale:** When volume data is absent, the volume confirmation filter is skipped (vol_ok=True) rather than blocking all signals with synthetic ones.

---

## STR-W — scanner_w_flags_pennants.py (PIVOT_DISTANCE=2)

### Fix 1: Look-ahead bias in consolidation pivot selection

**Before (line 130-132):**
```python
shs, _ = find_peaks(win_high, distance=PIVOT_DISTANCE)
sls, _ = find_peaks(-win_low, distance=PIVOT_DISTANCE)
if len(shs) < 2 or len(sls) < 2:
    continue
```

**After:**
```python
shs, _ = find_peaks(win_high, distance=PIVOT_DISTANCE)
sls, _ = find_peaks(-win_low, distance=PIVOT_DISTANCE)
# Exclude unconfirmed pivots within PIVOT_DISTANCE of window end
if len(shs) > 0:
    shs = shs[ce - wpos[shs] >= PIVOT_DISTANCE]
if len(sls) > 0:
    sls = sls[ce - wpos[sls] >= PIVOT_DISTANCE]
if len(shs) < 2 or len(sls) < 2:
    continue
```

**Rationale:** Same root cause as STR-V. Pivots found by `find_peaks` near the consolidation end (`ce`) are unconfirmed — they require PIVOT_DISTANCE future bars. The filter `ce - wpos[p] >= PIVOT_DISTANCE` ensures only confirmed pivots enter the trendline fit. `wpos` maps relative find_peaks indices to absolute bar positions.

### Fix 2: Deduplication — 83% duplicate signals

**Before (line 181):**
```python
return signals
```

**After:**
```python
# Deduplicate by (ticker, date, signal_type) — sliding window can
# generate the same signal multiple times. Keep first occurrence.
seen = set()
deduped = []
for sig in signals:
    key = (sig["ticker"], sig["date"], sig["signal_type"])
    if key not in seen:
        seen.add(key)
        deduped.append(sig)

return deduped
```

**Rationale:** The sliding mast_start loop and nested consolidation end loop can identify the same pattern from multiple starting points, generating identical (ticker, date, signal_type) tuples. The dedup keeps the first occurrence of each unique combination, eliminating the 83% duplication rate.

---

## STR-AB — scanner_ab_obv_divergence.py (SWING_WINDOW=2)

### Fix: Look-ahead bias in divergence entry timing

**Before (line 149, bullish path):**
```python
for j in range(p2_idx + 1, len(df)):
```

**After:**
```python
for j in range(p2_idx + SWING_WINDOW + 1, len(df)):
```

**Before (line 201, bearish path):**
```python
for j in range(p2_idx + 1, len(df)):
```

**After:**
```python
for j in range(p2_idx + SWING_WINDOW + 1, len(df)):
```

**Rationale:** The pivot detection uses a symmetric window of SWING_WINDOW bars on each side. A pivot low at `p2_idx` is only confirmed at `p2_idx + SWING_WINDOW` (when the right-side bars are observed). Starting entry search at `p2_idx + 1` uses the pivot before it's confirmed — a look-ahead bias. Shifting to `p2_idx + SWING_WINDOW + 1` ensures the pivot is fully confirmed before any entry decision.

---

## STR-AG — scanner_ag_wedge.py (PIVOT_DISTANCE=3)

### Fix: Look-ahead bias in pivot selection

**Before (line 92-93):**
```python
shs = [j for j in sh_idx if start <= j <= end]
sls = [j for j in sl_idx if start <= j <= end]
```

**After:**
```python
shs = [j for j in sh_idx if start <= j <= end - PIVOT_DISTANCE]
sls = [j for j in sl_idx if start <= j <= end - PIVOT_DISTANCE]
```

**Rationale:** Identical root cause as STR-V. Pivots within PIVOT_DISTANCE of the window end are unconfirmed by find_peaks and must be excluded from trendline fitting.

---

## Verification

```
$ cd ~/HermesForge/scripts/validation/scanners && python -c 'import scanner_v_triangles; import scanner_w_flags_pennants; import scanner_ab_obv_divergence; import scanner_ag_wedge; print("All 4 import OK")'
All 4 import OK
```

All 4 modules import cleanly. No syntax errors.

## Git Commit

```
US-114 coder: Fix look-ahead + dedup in STR-V, STR-W, STR-AB, STR-AG
```

Files changed:
- scripts/validation/scanners/scanner_v_triangles.py
- scripts/validation/scanners/scanner_w_flags_pennants.py
- scripts/validation/scanners/scanner_ab_obv_divergence.py
- scripts/validation/scanners/scanner_ag_wedge.py
