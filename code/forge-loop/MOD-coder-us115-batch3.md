# US-115 Coder Batch 3 — STR-R, STR-B (+ STR-W classification)

**Coder:** Coder agent (T2, glm-5.2)
**Date:** 2026-08-16
**Status:** COMPLETE — committed as c3422fe
**Design doc:** `~/HermesForge/04-ForgeLoop/DESIGN-architect-US115-market-structure.md`

---

## Summary

Modified 2 of 3 assigned scanners to use the `market_structure` module for
entry/stop/target derivation. The third (STR-W) was inspected and reclassified
to KEEP (pattern-derived targets).

| Scanner | Action | STRATEGY_VERSION | Trades (SPY) |
|---------|--------|-----------------|--------------|
| STR-R (Alligator) | MODIFIED → v2.0 | 2.0 | 6 |
| STR-B (MACD Div) | MODIFIED → v2.0 | 2.0 | 15 |
| STR-W (Flags/Pennants) | KEEP (not modified) | 1.0 | — |

---

## STR-R — Williams Alligator Trend (MODIFIED)

### What changed

1. **Import:** Added `from market_structure import compute_structure_trade`
   with `sys.path.insert(0, str(Path(__file__).parent))` guard.

2. **Entry/stop/target:** Replaced `entry=close[i]`, `stop=1.5*ATR`,
   `target=3R` with `compute_structure_trade(result, signal_idx=i, ...)`.
   The Alligator lines (Jaw/Teeth/Lips) remain the signal trigger — only
   entry/stop/target derivation changed.

3. **Alligator sleep exit retained:** The `_walk_forward_exit` still checks
   for Alligator lines tangling during the hold period (sleep exit). This is
   a time-stop variant unique to STR-R. The `r_multiple` for sleep exits is
   computed dynamically from actual prices (not hardcoded 0).

4. **Target R made dynamic:** `_walk_forward_exit` target exits now compute
   `r_multiple = gain / risk` dynamically instead of returning hardcoded
   `TARGET_RR` (3.0). Stop exits remain -1.0R by construction.

5. **entry_idx propagation:** Signal dict includes `entry_idx` (df-positional)
   and `entry_date`. `run_backtest()` uses `sig["entry_idx"]` for the exit
   walk start, falling back to date-based lookup for legacy signals.

6. **entry_idx conversion fix:** STR-R's `scan()` works on `result` (the
   dropna'd DataFrame from `compute_alligator`), but `run_backtest()` passes
   the original `df` to `_walk_forward_exit`. The entry_idx from
   `compute_structure_trade` is positional relative to `result`. Added
   conversion: `df_entry_idx = int(df.index.get_loc(result.index[trade["entry_idx"]]))`
   to map from result-positional to df-positional.

7. **Cooldown guard:** 20-bar per-ticker cooldown (`COOLDOWN_BARS = 20`).
   After a signal is accepted (`compute_structure_trade` returns non-None),
   all subsequent signals on that ticker are skipped for 20 bars.

8. **Constants removed:** `TARGET_RR = 3.0` and `STOP_ATR_MULT = 1.5` removed.
   Added `COOLDOWN_BARS = 20`.

9. **STRATEGY_VERSION** bumped from `"1.0"` to `"2.0"`.

### SPY backtest results

```
Trades: 6
Win rate: 33.3%
Avg R: 0.104
Exit types: stop=3, target=2, sleep=1
Entry types: market=4, pullback=2
Pullback offsets: 0 (market), 3, 5 bars
```

---

## STR-B — MACD Histogram Divergence (MODIFIED)

### What changed

1. **Import:** Added `from market_structure import compute_structure_trade`
   with `sys.path.insert(0, str(Path(__file__).parent))` guard.

2. **Architecture change:** STR-B has a different architecture from other
   scanners — `scan()` does exit simulation inline (via `_simulate_exit`),
   not in a separate `run_backtest()`. `_check_signal` previously returned
   `(entry_price, stop_price, target_price, conf_level, macd_bars, extra)`.
   Now returns `(crossover_bar, conf_level, macd_bars, extra)` — entry/stop/
   target computation moved to `scan()` via `compute_structure_trade`.

3. **Crossover bar as signal_idx:** `_check_signal` now tracks the actual
   crossover bar (`j = i + offset`) and returns it. `scan()` passes this as
   `signal_idx` to `compute_structure_trade`. This is more correct than the
   old code which used `close_arr[i]` (the divergence bar) even when the
   crossover occurred 1-2 bars later.

4. **Entry/stop/target:** Replaced `entry=close[i]`, `stop=0.5*ATR`,
   `target=lowest_low_20_bars` with `compute_structure_trade(df,
   signal_idx=crossover_bar, ...)`. The crude structure target (lowest low
   in 20 bars) is replaced by proper `compute_natural_target` (nearest
   confirmed overhead/below resistance meeting min_rr=1.5).

5. **Exit simulation:** `_simulate_exit` now starts from `trade["entry_idx"]`
   (the pullback fill bar), not `i` (the signal bar). This ensures the exit
   walk doesn't simulate stops/targets during the pullback wait window.

6. **R-multiple dynamic:** `realised_r` is computed from `trade["entry_price"]`
   and `trade["risk"]` (both from `compute_structure_trade`), not from the
   old `entry_price`/`stop_price` variables.

7. **Cooldown guard:** 20-bar per-ticker cooldown, same pattern as STR-R.

8. **Constants removed:** `MIN_RR = 3.0`, `ATR_STOP_MULT = 0.5`,
   `TARGET_LOOKBACK = 20` removed. Added `COOLDOWN_BARS = 20`,
   `STRATEGY_VERSION = "2.0"`.

9. **Signal dict enriched:** Added `entry_date`, `entry_idx`, `risk`, `rr`,
   `entry_type`, `strategy_version` fields.

### SPY backtest results

```
Signals: 15
Win rate: 20.0%
Avg R: -0.570
Exit reasons: stop=11, time=2, target=2
Entry types: pullback=12, market=3
```

---

## STR-W — Flags and Pennants (KEEP — NOT MODIFIED)

### Inspection result

STR-W uses **pattern-derived targets** (mast height projected from breakout):

```python
# Long: target = entry + mast_h (line 173)
target = entry + mast_h

# Short: target = entry - mast_h (line 183)
target = entry - mast_h
```

Where `mast_h = close[mast_end] - close[mast_start]` (bullish) or
`mast_h = close[mast_start] - close[mast_end]` (bearish).

This is a pattern-measured target, identical in spirit to STR-AG (wedge
height) and STR-T (neckline projection). Per design doc §3.3:

> **STR-W (Flags/Pennants):** Flag/pennant is the trigger. Pattern pole height
> is currently used for target in some variants; if W already uses
> pattern-measured targets it should arguably move to KEEP — **the coder
> must inspect W and reclassify it to KEEP if its target is pattern-derived
> (pole height), matching AG.**

**Decision: KEEP.** STR-W's target is pattern-derived (mast/pole height).
Forcing the `market_structure` module would discard the pattern-specific R
geometry. STR-W remains at STRATEGY_VERSION = "1.0".

---

## Verification

### Import test
```
cd ~/HermesForge/scripts/validation/scanners
python -c 'import scanner_r_alligator; import scanner_b_macd_divergence; print("Both import OK")'
# Output: Both import OK
```

### Look-ahead bias check
```
MARKET_STRUCTURE_DEBUG=1 python -c '...'
# STR-R: 6 trades — no look-ahead assertion errors
# STR-B: 15 signals — no look-ahead assertion errors
# All look-ahead assertions passed.
```

### entry_idx verification
- STR-R: entry_idx correctly converted from result-positional to df-positional.
  Pullback offsets: 0 (market), 3, 5 bars verified.
- STR-B: entry_idx verified as df-positional (assertion passed for all signals).

### Stale constant check
- No references to `TARGET_RR`, `STOP_ATR_MULT`, `MIN_RR`, `ATR_STOP_MULT`,
  or `TARGET_LOOKBACK` remain in either modified scanner's code.

---

## Commit

```
c3422fe US-115: Modify STR-R, STR-B (+ STR-W if applicable) to use market_structure module
```

---

## Notes for risk-guardian / validation

1. **STR-R entry_idx fix:** The previous batch 2 commit (ad2ab9b) had a bug
   where `entry_idx` from `compute_structure_trade` was positional relative
   to `result` (the dropna'd Alligator DataFrame), but `run_backtest()` used
   it with the original `df`. This caused the exit walk to start at the
   wrong bar. Fixed in this commit with date-based index conversion.
   Impact: STR-R SPY win rate corrected from 16.7% to 33.3%.

2. **STR-B crossover bar:** Using the actual crossover bar (not the
   divergence bar) as `signal_idx` for `compute_structure_trade` is more
   correct. The old code used `close[i]` even when the crossover was at
   `i+2`, entering at a stale price. The new code enters at the pullback
   after the crossover bar.

3. **Trade count expectations:** Per design doc §5.5, structure-based
   filtering (min_rr skip + pullback) should reduce signal count 20-50%.
   STR-R has only 6 trades on SPY — this is expected for a rare-signal
   strategy (Alligator awakening from sleep). STR-B has 15 signals.
   Validation should compare v1.x vs v2.x on win-rate, avg R, profit factor,
   AND trade count.
