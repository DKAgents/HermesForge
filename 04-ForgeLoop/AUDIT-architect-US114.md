# US-114 Architectural Audit: 19 Strategy Scanners

**Auditor:** Architect agent (architect profile, T2)
**Date:** 2026-08-16
**Scope:** 19 scanner files in `~/HermesForge/scripts/validation/scanners/` built without architectural review.
**Audit dimensions:** (1) Look-ahead bias / future data leakage, (2) Interface consistency, (3) Code quality.

---

## Summary Table

| # | Scanner | Verdict | Issues | Severity |
|---|---------|---------|--------|----------|
| 1 | scanner_s_elliott_wave.py | **FAIL** | 3 | CRITICAL |
| 2 | scanner_t_head_shoulders.py | **FAIL** | 3 | CRITICAL |
| 3 | scanner_u_double_top_bottom.py | **FAIL** | 3 | CRITICAL |
| 4 | scanner_v_triangles.py | **FAIL** | 4 | HIGH |
| 5 | scanner_w_flags_pennants.py | **NEEDS-FIX** | 3 | MEDIUM |
| 6 | scanner_x_parabolic_sar.py | **PASS** | 1 | LOW |
| 7 | scanner_y_adx_dmi.py | **PASS** | 1 | LOW |
| 8 | scanner_z_stochastic.py | **PASS** | 1 | LOW |
| 9 | scanner_aa_williams_r.py | **PASS** | 1 | LOW |
| 10 | scanner_ab_obv_divergence.py | **NEEDS-FIX** | 2 | MEDIUM |
| 11 | scanner_ac_cci.py | **PASS** | 1 | LOW |
| 12 | scanner_ad_keltner.py | **NEEDS-FIX** | 2 | LOW |
| 13 | scanner_ae_4week_rule.py | **PASS** | 0 | NONE |
| 14 | scanner_af_candlestick.py | **PASS** | 1 | LOW |
| 15 | scanner_ag_wedge.py | **NEEDS-FIX** | 3 | MEDIUM |
| 16 | scanner_ah_island_reversal.py | **PASS** | 1 | LOW |
| 17 | scanner_ai_seasonal.py | **PASS** | 1 | LOW |
| 18 | scanner_aj_intermarket.py | **NEEDS-FIX** | 2 | MEDIUM |
| 19 | scanner_r_alligator.py | **NEEDS-FIX** | 4 | MEDIUM |

**Totals:** 4 FAIL, 6 NEEDS-FIX, 9 PASS.

---

## Systemic Findings (affect all 19 scanners)

### S1. Signal dict uses `ticker` instead of `symbol` (interface deviation, all 19)
Every scanner's `scan()` returns dicts with key `"ticker"` rather than the contract-specified `"symbol"`. The downstream `run_backtest()` functions DO emit `"symbol": ticker` in trade dicts, creating an inconsistency: scan-output consumers get `ticker`; backtest-output consumers get `symbol`. Any orchestrator that reads scan() output and expects `symbol` will fail silently. **Fix:** rename `ticker` → `symbol` in all 19 scan() return dicts (or add both keys).

### S2. Entry at signal-bar close (mild optimistic bias, all 19)
All scanners enter at `close[i]` of the signal bar. In live trading, the close is only known at bar end and execution would occur at next-bar open. This is a universal convention here, not strict look-ahead, but it systematically overstates fill quality. Out of scope for the FAIL/NEEDS-FIX verdicts below but worth noting.

### S3. `import sys` unused (code quality, 14 of 19)
STR-S/T/U/V/W/X/Y/Z/AA/AB/AC/AD/AG/AH import `sys` but never reference it. Harmless but noisy. (STR-AI and STR-AJ also import sys unused; STR-R uses `sys.path.insert`.)

---

## Detailed Findings Per Scanner

### 1. scanner_s_elliott_wave.py — STR-S — FAIL (CRITICAL)

**1a. LOOK-AHEAD BIAS (CRITICAL) — lines 52-58, 90-146, 150-199**
`_find_pivots()` (lines 52-58) uses `scipy.signal.find_peaks(high, distance=3)`. A peak at index `p` requires bars `p+1`, `p+2`, `p+3` to confirm (distance=3 means no higher peak within 3 bars on either side). The scanner then identifies A-B-C corrective pivots (lines 106-124) and enters at `for j in range(c_idx + 1, min(c_idx + 15, n))` (line 135). At bar `c_idx+1`, the C pivot at `c_idx` is NOT yet confirmable — it needs `c_idx+3`. Entries at `c_idx+1` and `c_idx+2` use the knowledge that `c_idx` is a swing low, which requires future data. Same issue in bearish path (lines 188-199, entry at `c_idx+1` after an unconfirmed swing high). The 5-wave impulse pivots (lines 90-93) and B pivot (line 115) have the same problem but are typically confirmed by the time the entry occurs (since A/B/C come after); the critical leak is the C pivot + early entry.

**Fix:** Start entry search at `c_idx + PIVOT_DISTANCE` (i.e., `c_idx + 3`) instead of `c_idx + 1`.

**1b. Interface — `ticker` not `symbol` (line 75).** See systemic S1.

**1c. Code quality — inline magic number 15 (lines 135, 188).** The `min(c_idx + 15, n)` search window uses a hardcoded 15 with no named constant. Should be `ENTRY_SEARCH_WINDOW = 15`.

---

### 2. scanner_t_head_shoulders.py — STR-T — FAIL (CRITICAL)

**2a. LOOK-AHEAD BIAS (CRITICAL) — lines 53-58, 92-132, 135-170**
`_find_pivots()` uses `find_peaks(distance=5)` (PIVOT_DISTANCE=5). A swing high at `R_idx` (line 93) needs `R_idx+5` to confirm. Entry occurs at `for j in range(R_idx + 1, min(R_idx + 15, n))` (line 117). Entries at `R_idx+1` through `R_idx+4` use the unconfirmed pivot. The troughs `t1` and `t2` (lines 100-105) are swing lows confirmed 5 bars later; the neckline is computed from these. Inverse H&S (lines 135-170) has the identical problem with swing lows and peaks.

**Fix:** Start entry search at `R_idx + PIVOT_DISTANCE` (i.e., `R_idx + 5`).

**2b. Interface — `ticker` not `symbol` (line 76).** See S1.

**2c. Code quality — `TARGET_RR = None` with None sentinel (line 34, 187, 226-232).** Target R is variable (pattern-based), so `_walk_forward_exit` returns `r_multiple: None` for target exits and `run_backtest` recomputes. This None-sentinel pattern is fragile and differs from all fixed-R scanners. Should compute R inline in the exit function.

---

### 3. scanner_u_double_top_bottom.py — STR-U — FAIL (CRITICAL)

**3a. LOOK-AHEAD BIAS (CRITICAL) — lines 49-54, 86-115, 118-145**
`_find_pivots()` uses `find_peaks(distance=4)` (PIVOT_DISTANCE=4). Double-top entry at `for j in range(p2_idx + 1, min(p2_idx + 15, n))` (line 103). `p2_idx` (line 88) is a swing high confirmed only at `p2_idx+4`. Entries at `p2_idx+1..p2_idx+3` are look-ahead. Double-bottom path (lines 118-145, entry at `t2_idx+1`) has the same issue with swing lows.

**Fix:** Start entry search at `p2_idx + PIVOT_DISTANCE` (`p2_idx + 4`).

**3b. Interface — `ticker` not `symbol` (line 72).** See S1.

**3c. Code quality — None-sentinel for variable R (line 162, 200-206).** Same issue as STR-T 2c.

---

### 4. scanner_v_triangles.py — STR-V — FAIL (HIGH)

**4a. LOOK-AHEAD BIAS (HIGH) — lines 49-54, 98-148**
`_find_pivots()` uses `find_peaks(distance=3)`. The window pivots are collected as `shs = [j for j in sh_idx if start <= j <= end]` (line 100). The breakout bar is `brk_idx = end + 1` (line 124). Any pivot at position `end`, `end-1`, or `end-2` is NOT confirmed by `end+1` (needs `pivot+3`). These unconfirmed pivots are used to fit the upper/lower trendlines (`_fit_line`, lines 105-106) and the breakout threshold (`upper_at_end`, line 109). The entry decision `if c > upper_at_end` (line 134) thus depends on a trendline derived from future-confirmed pivots. Less severe than STR-S/T/U because the entry isn't always 1 bar after a specific pivot, but the trendline fit is contaminated.

**Fix:** Exclude pivots within `PIVOT_DISTANCE` of `end` from the window, or only use pivots confirmed by `end+1`.

**4b. VOLUME EDGE-CASE BUG (HIGH) — lines 77, 129**
`vol = df["volume"].values if "volume" in df.columns else np.ones(n)` (line 77). When volume is absent, `vol = 1` for all bars, `avg_vol = 1`, and `vol_ok = v >= VOLUME_MULT * av` becomes `1 >= 1.5 * 1 = False` (line 129). **Result: zero signals for any asset without a volume column** (some crypto pairs). Silent failure — no warning, just empty output.

**Fix:** If no volume column, set `vol_ok = True` (skip volume filter) rather than using synthetic ones.

**4c. Interface — `ticker` not `symbol` (line 84).** See S1.

**4d. Code quality — magic numbers in classification (lines 121-122).** `flat_band / 10` is an unnamed heuristic. The `0.6` convergence threshold doesn't appear here but the flat-detection divisor `10` is unexplained.

---

### 5. scanner_w_flags_pennants.py — STR-W — NEEDS-FIX (MEDIUM)

**5a. LOOK-AHEAD BIAS (MEDIUM) — lines 130-131, 124-165**
`find_peaks(win_high, distance=PIVOT_DISTANCE)` with `PIVOT_DISTANCE=2` (line 34) is called on the consolidation slice `high[mast_end+1:ce+1]` (line 125). The breakout is at `brk_idx = ce + 1` (line 155). Pivots at `ce` or `ce-1` are not confirmed by `ce+1` (need `pivot+2`). These unconfirmed pivots feed `_fit_slope` (lines 134-135) and the extrapolated `upper`/`lower` line values at `ce` (lines 149-150), which set the breakout threshold.

**Fix:** Start consolidation window at least `PIVOT_DISTANCE` bars before `ce`, or exclude the last `PIVOT_DISTANCE` bars from pivot detection.

**5b. Interface — `ticker` not `symbol` (line 75).** See S1.

**5c. Code quality — inline magic numbers (lines 142-143).** `0.6` convergence threshold, `1e-9` epsilon, `PARALLEL_TOL=0.25` — the 0.6 is unnamed. `_fit_slope` (line 51) lacks a docstring.

---

### 6. scanner_x_parabolic_sar.py — STR-X — PASS (LOW)

**6a. Look-ahead: NONE.** SAR is computed iteratively forward (lines 77-113). `sar[i]` uses only `sar[i-1]`, `ep` (tracked from past), and bar `i`'s high/low/close. The clamp `min(new_sar, low.iloc[i-1], low.iloc[i-2])` (line 88) uses past bars. Flip detection (lines 145-149) compares `sar[i-1]` vs `close[i-1]` and `sar[i]` vs `close[i]` — all causal. Entry at `close[i]`. Clean.

**6b. Interface — `ticker` not `symbol` (line 164).** See S1.

**Minor:** Redundant ternary `low.iloc[i - 2] if i >= 2 else low.iloc[i - 1]` (lines 88, 102) — the loop starts at `i=2` so `i >= 2` is always true. Cosmetic.

---

### 7. scanner_y_adx_dmi.py — STR-Y — PASS (LOW)

**7a. Look-ahead: NONE.** ADX/+DI/-DI computed with `shift(1)` for directional movement (lines 55-57). Cross detection at bar `i` compares `plus_di[i-1]` vs `minus_di[i-1]` and `plus_di[i]` vs `minus_di[i]` (lines 117-119). Entry at `close[i]`. All causal.

**7b. Interface — `ticker` not `symbol` (line 135).** See S1.

**Minor:** `import sys` unused (line 22).

---

### 8. scanner_z_stochastic.py — STR-Z — PASS (LOW)

**8a. Look-ahead: NONE.** Stochastic %K/%D use `rolling()` windows (lines 52-58). Cross at bar `i` uses `k_arr[i-1]`, `d_arr[i-1]`, `k_arr[i]`, `d_arr[i]` (lines 89-91). Entry at `close[i]`. Causal.

**8b. Interface — `ticker` not `symbol` (line 105).** See S1.

**Minor:** `import sys` unused (line 22).

---

### 9. scanner_aa_williams_r.py — STR-AA — PASS (LOW)

**9a. Look-ahead: NONE.** Williams %R uses `rolling()` (lines 53-56). Cross at bar `i` uses `wr_arr[i-1]` and `wr_arr[i]` (lines 84-86). Entry at `close[i]`. Causal.

**9b. Interface — `ticker` not `symbol` (line 99).** See S1.

**Minor:** `import sys` unused (line 24).

---

### 10. scanner_ab_obv_divergence.py — STR-AB — NEEDS-FIX (MEDIUM)

**10a. LOOK-AHEAD BIAS (MEDIUM, 1 bar) — lines 58-84, 149-154, 201-206**
`_find_pivots()` (lines 58-84) uses a symmetric window: `right = arr[i + 1:i + 1 + window]` with `window=2` (SWING_WINDOW). A pivot at `p2_idx` requires bars `p2_idx+1` and `p2_idx+2` to confirm. The entry search starts at `for j in range(p2_idx + 1, len(df))` (line 149). At `p2_idx+1`, the pivot is not yet confirmed (needs `p2_idx+2`). This is 1 bar of look-ahead — less severe than the find_peaks scanners but still real.

**Fix:** Start entry search at `p2_idx + SWING_WINDOW + 1` (i.e., `p2_idx + 3`).

**10b. Interface — `ticker` not `symbol` (line 167).** See S1.

---

### 11. scanner_ac_cci.py — STR-AC — PASS (LOW)

**11a. Look-ahead: NONE.** CCI uses `rolling(window=period)` on typical price (lines 52-60). Cross at bar `i` uses `cci_arr[i-1]` and `cci_arr[i]` (lines 89-91). Entry at `close[i]`. Causal.

**11b. Interface — `ticker` not `symbol` (line 104).** See S1.

**Minor:** `import sys` unused (line 23).

---

### 12. scanner_ad_keltner.py — STR-AD — NEEDS-FIX (LOW)

**12a. Look-ahead: NONE.** Keltner bands from `ewm(span=EMA_PERIOD)` and `ewm(alpha=1/ATR_PERIOD)` (lines 41-53). Breakout detection compares `close > upper` with `prev_close <= prev_upper` (line 97). All causal.

**12b. Interface — `ticker` not `symbol` (line 106).** See S1.

**12c. Code quality — FORMAT BUG (line 252).**
```python
print(f"Max win: {df['r_multiple'].max():3f}R")
```
Missing the dot: `:3f` should be `:.3f`. This prints the full unrounded float (e.g., `3.0R` instead of `3.000R`). Cosmetic but inconsistent with all other scanners.

---

### 13. scanner_ae_4week_rule.py — STR-AE — PASS (NONE)

**13a. Look-ahead: NONE — gold standard.** Donchian channel explicitly uses `.shift(1)` to exclude the current bar (lines 43-44): `upper = high.rolling(CHANNEL_PERIOD).max().shift(1)`. This is the correct way to detect breakouts — the channel is built from prior bars only, and the current bar's close is compared against it. No future data anywhere.

**13b. Interface — `ticker` not `symbol` (line 82).** See S1.

**No other issues.** This scanner is the reference implementation for look-ahead-free breakout detection. The `shift(1)` pattern should be adopted by STR-S/T/U/V/W/AG.

---

### 14. scanner_af_candlestick.py — STR-AF — PASS (LOW)

**14a. Look-ahead: NONE.** All candlestick patterns use current and prior bars only: 1-bar patterns at bar `i` (lines 84-93), 2-bar at `i` and `i-1` (lines 96-106), 3-bar at `i`, `i-1`, `i-2` (lines 109-133). No `i+1` references. Entry at `close[i]`. Causal.

**14b. Interface — `ticker` not `symbol` (line 171).** See S1.

**Minor:** Inline magic numbers `0.35` (line 87), `2 * body` (lines 90, 92), `0.4` (line 117) — unnamed thresholds for body/wick ratios.

---

### 15. scanner_ag_wedge.py — STR-AG — NEEDS-FIX (MEDIUM)

**15a. LOOK-AHEAD BIAS (MEDIUM) — lines 46-51, 90-145**
Identical structure to STR-V. `_find_pivots()` uses `find_peaks(distance=3)`. Window pivots in `[start, end]` (lines 92-93). Breakout at `brk_idx = end + 1` (line 120). Pivots at `end`, `end-1`, `end-2` are unconfirmed at `end+1` but feed the trendline fit (lines 96-97) and the extrapolated line values `upper_at_end`/`lower_at_end` (lines 117-118) used for the breakout threshold.

**Fix:** Exclude pivots within `PIVOT_DISTANCE` of `end`, or confirm pivots before `end - PIVOT_DISTANCE`.

**15b. Interface — `ticker` not `symbol` (line 78).** See S1.

**15c. Code quality — None-sentinel for variable R (line 162, 200-206).** Same pattern as STR-T/U.

---

### 16. scanner_ah_island_reversal.py — STR-AH — PASS (LOW)

**16a. Look-ahead: NONE.** Gaps computed from `prev_high = df["high"].shift(1)` and `prev_low = df["low"].shift(1)` (lines 45-46). Island detection looks BACK from bar `i` for prior gaps (lines 72-73, `j = i - k - 1`). Entry at `close[i]`. All causal.

**16b. Interface — `ticker` not `symbol` (line 95).** See S1.

**Minor:** `import sys` unused (line 29).

---

### 17. scanner_ai_seasonal.py — STR-AI — PASS (LOW)

**17a. Look-ahead: NONE — explicitly expanding window.** `_expanding_month_pos_rate()` (lines 74-107) computes the positive/negative rate for each calendar month using ONLY completed prior months: `mr_sorted["month_end"].dt.to_period("M") < cur_ym` (line 96). The strict `<` ensures the current month is never included. The docstring (lines 16-18) explicitly documents this. Clean.

**17b. Interface — `ticker` not `symbol` (line 142).** See S1.

**Minor — PERFORMANCE (lines 92-107):** `_expanding_month_pos_rate` is O(n*m) — for each of n bars, it filters the entire monthly-returns table. On multi-year daily data (~5000 bars, ~60 months) this is ~300K comparisons, acceptable. On larger datasets it would be slow. Could be optimized with cumulative counters per calendar month.

---

### 18. scanner_aj_intermarket.py — STR-AJ — NEEDS-FIX (MEDIUM)

**18a. INTERFACE DEVIATION (MEDIUM) — lines 173-174**
```python
def scan(df: pd.DataFrame, ticker: str, long_only: bool = False,
         intermarket: pd.DataFrame = None) -> list:
```
The `scan()` signature adds a 4th parameter `intermarket` that is functionally required. If called with the standard 3-arg contract (`scan(df, ticker, long_only)`), `intermarket=None` and the function returns `[]` immediately (line 178). **The scanner is non-functional under the standard interface.** An orchestrator that calls all scanners uniformly with `(df, ticker, long_only)` will get zero signals from STR-AJ with no error.

**Fix:** Either (a) make STR-AJ fetch intermarket data internally when `intermarket=None`, or (b) document it as a special-case scanner excluded from uniform dispatch, or (c) have the orchestrator pre-load and pass intermarket data.

**18b. Look-ahead: NONE.** DXY/TNX slopes use `rolling(SLOPE_WINDOW).apply(...)` (line 74). `risk_on_trigger` uses `risk_on.shift(1, fill_value=False)` (line 163) — causal. Entry at `close[i]`. Clean.

**18c. Interface — `ticker` not `symbol` (line 217).** See S1.

---

### 19. scanner_r_alligator.py — STR-R — NEEDS-FIX (MEDIUM)

**19a. Look-ahead: NONE.** Alligator lines use `_smma(median_price, N).shift(K)` (lines 94-96). `.shift(8)` moves SMMA values forward in time, so `jaw[i] = smma(median)[i-8]` — past data projected forward (standard Alligator display). At bar `i`, `lips = smma5[i-3]`, `teeth = smma8[i-5]`, `jaw = smma13[i-8]`. The signal at bar `i` compares `close[i]` to lines derived from data at `i-3` or earlier. Causal. No future data.

**19b. INTERFACE — fragile `date` field (lines 176, 201).**
```python
"date": row.name if hasattr(row.name, 'strftime') else str(row.get("date", i)),
```
For a DatetimeIndex, `row.name` is a Timestamp and has `strftime` — works. But `row.get("date", i)` on a pandas Series row looks for a COLUMN named "date" (which doesn't exist — date is the index), so the fallback returns `i` (an integer). If the index is ever not a DatetimeIndex (e.g., RangeIndex after some operation), `date` becomes an int. All other scanners use `df.index[i]` directly. **Inconsistent and fragile.**

**Fix:** Use `df.index[i]` or `result.index[i]` directly like every other scanner.

**19c. CODE BUG — sleep exit hardcodes r_multiple=0 (lines 249-259).**
```python
if last["alligator_sleeping"]:
    exit_price = df.iloc[i]["close"]
    return {"exit_type": "sleep", "exit_price": exit_price,
            "bars_held": i - entry_idx, "r_multiple": 0}  # simplified
```
The R-multiple is hardcoded to `0` regardless of the actual exit price vs entry. A sleep exit at a profit or loss is recorded as break-even. This distorts backtest statistics. **Fix:** compute `r_multiple` from `exit_price`, `entry_price`, and `risk` like the time-stop path does.

**19d. PERFORMANCE — O(n²) recomputation (lines 249-250).**
```python
for i in range(entry_idx + 1, min(entry_idx + max_bars + 1, n)):
    r = compute_alligator(df.iloc[:i+1])
```
`compute_alligator` is called for every bar in the holding window, each time processing all bars from 0 to `i`. For a 20-bar hold on a 5000-bar dataset, this is 20 × ~5000 = 100K rows processed per trade. With many trades, this is extremely slow. **Fix:** precompute `compute_alligator(df)` once and index into it, or compute the sleeping flag inline.

**19e. Interface — `ticker` not `symbol` (line 177).** See S1.

**19f. CODE — stricter entry-end check (line 292).**
```python
if entry_idx + MAX_HOLD_BARS >= len(df):
    continue
```
All other scanners use `entry_idx + 1 >= len(df)` (allow trades with at least 1 future bar). STR-R requires a full `MAX_HOLD_BARS` window, silently dropping valid signals near the end of data. Inconsistent with the other 18.

---

## Priority Remediation Order

1. **CRITICAL (look-ahead, backtest results invalid):** STR-S, STR-T, STR-U — fix entry search to start at `pivot_idx + PIVOT_DISTANCE`.
2. **HIGH (look-ahead + silent volume bug):** STR-V — fix pivot window exclusion AND volume fallback.
3. **MEDIUM (look-ahead, partial):** STR-W, STR-AG — fix pivot window exclusion near breakout bar.
4. **MEDIUM (1-bar look-ahead):** STR-AB — start entry search at `p2_idx + SWING_WINDOW + 1`.
5. **MEDIUM (interface):** STR-AJ — make `scan()` work with standard 3-arg contract or document exception.
6. **MEDIUM (code bugs):** STR-R — fix r_multiple=0 sleep exit, O(n²) recomputation, fragile date field.
7. **LOW (cosmetic):** STR-AD format bug (line 252); all 19 — `ticker` → `symbol` rename; remove unused `import sys`.

---

## Methodology Notes

- **find_peaks look-ahead verification:** Confirmed empirically — `scipy.signal.find_peaks(x, distance=N)` requires N future bars beyond a peak to confirm it, because the `distance` parameter removes lower peaks within N bars of a higher one. A peak at index `p` is only "final" once bars `p+1` through `p+N` are observed. See verification output: a peak at idx 2 with `distance=3` suppresses a local max at idx 4, which is only determinable after observing idx 5.
- **Scanners confirmed clean (no look-ahead):** STR-X, STR-Y, STR-Z, STR-AA, STR-AC, STR-AD, STR-AE, STR-AF, STR-AH, STR-AI, STR-AJ, STR-R — all use causal rolling/shift operations or causal iterative computation.
- **STR-AE (Donchian) is the reference implementation** — its explicit `.shift(1)` to exclude the current bar from the channel is the pattern all breakout scanners should follow.
- All 19 scanners were read in full; line numbers reference the files as they exist at audit time.
