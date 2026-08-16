# DESIGN — US-115: Unified Market Structure Module

**Architect:** Architect agent (T2, glm-5.2)
**Date:** 2026-08-16
**Status:** DESIGN ONLY — implementation delegated to coder (ADR-001 T2 floor)
**Target module:** `~/HermesForge/scripts/validation/scanners/market_structure.py`
**Supersedes:** arbitrary entry/stop/target logic across 11 indicator-based LIVE scanners
**Predecessor lessons:** US-114 (find_peaks `distance=N` requires N future bars to confirm; entry must start at `pivot + PIVOT_DISTANCE`, not `pivot + 1`)

---

## 0. Problem Statement (context for the coder)

11 of 15 LIVE scanners enter at `close[signal_idx]` (buying local highs on strength), place stops at fixed ATR multiples (1.0 / 1.5 / 2.0 × ATR) disconnected from structure, and target a fixed 3R (or 2R for candlestick). A discretionary SMC/ICT trader instead:

1. Waits for a pullback to support after the signal,
2. Enters at that support level (limit order),
3. Places the stop below the structure that invalidates the thesis (the swing low that defined the support),
4. Targets the next natural resistance overhead.

This document specifies a single shared, look-ahead-free module that all 11 indicator-based scanners call to derive `entry_price`, `entry_idx`, `stop_price`, and `target_price` from market structure rather than fixed parameters.

---

## 1. Module API

File: `~/HermesForge/scripts/validation/scanners/market_structure.py`

The module exposes **three primitive functions** (as requested) plus **one orchestrator convenience function** that wires them in the correct, look-ahead-safe order. Scanners SHOULD call the orchestrator; the primitives are exposed for unit testing and for scanners that need custom ordering.

### Shared parameters / conventions

- `df`: a `pd.DataFrame` with a `DatetimeIndex` and lowercase columns `open, high, low, close` (volume optional). Scanners already normalize to this form.
- `decision_idx`: integer positional index of the bar at which the structure decision is made. This is the **no-look-ahead cutoff**: only pivots confirmed at or before `decision_idx` may be used.
  - For market-entry trades: `decision_idx = signal_idx`.
  - For pullback-entry trades: `decision_idx = entry_idx` (the bar at which the pullback limit order actually fills, which is `>= signal_idx`). Using `entry_idx` for stop/target is *stricter* (more pivots confirmed) than using `signal_idx` and is therefore safe.
- `direction`: `"long"` or `"short"`.
- `PIVOT_DISTANCE`: module-level constant, default `5` (matches STR-T/STR-S convention). A pivot at positional index `p` is **confirmed** at bar `p + PIVOT_DISTANCE` (because `scipy.signal.find_peaks(distance=N)` requires N bars on each side with no higher/lower peak).
- `atr`: optional precomputed `pd.Series`. If `None`, the module computes Wilder ATR(14) internally (same formula as every scanner's `_compute_atr`). Passing it in avoids recompute when a scanner already has it.

### 1.1 `compute_pullback_entry`

```python
def compute_pullback_entry(
    df: pd.DataFrame,
    signal_idx: int,
    direction: str,
    max_wait_bars: int = 5,
    pivot_distance: int = PIVOT_DISTANCE,
    ema_span: int = 20,
    fallback: str = "signal",   # "signal" | "window_end"
) -> tuple[float, int]:
    """
    After a signal fires at signal_idx, wait up to max_wait_bars for price to
    pull back to the nearest confirmed support, then enter via limit order at
    that support.

    Long : support = nearest confirmed swing low below close[signal_idx]
           OR rising EMA(ema_span) below close[signal_idx], whichever is closer
           to the close (i.e., the first level price would test on a dip).
    Short: mirror (nearest confirmed swing high above close, OR falling EMA).

    A pullback "occurs" when, on bar j in (signal_idx, signal_idx+max_wait_bars],
    the bar's low (long) / high (short) reaches the support level:
        long : low[j]  <= support_level   -> fill at support_level (limit buy)
        short: high[j] >= support_level   -> fill at support_level (limit sell)

    Limit-fill refinement: if the bar opens beyond the level (gap), fill at
    the open (better price for the buyer/seller) rather than the limit.

    Returns:
        (entry_price, entry_idx)
          - entry_idx = j (the bar where the limit filled), OR
          - fallback: (close[signal_idx], signal_idx) if fallback="signal"
                     (close[signal_idx+max_wait_bars], that idx) if fallback="window_end"
          - fallback is used when no pullback touch occurs within the window.
    """
```

**Return type:** `tuple[float, int]` — always returns a valid entry; never `None`. (The decision to skip a trade belongs to `compute_natural_target`, not entry.)

### 1.2 `compute_structure_stop`

```python
def compute_structure_stop(
    df: pd.DataFrame,
    decision_idx: int,
    direction: str,
    entry_price: float,
    max_atr: float = 2.0,
    min_atr: float = 0.5,
    lookback: int = 20,
    pivot_distance: int = PIVOT_DISTANCE,
    atr: pd.Series | None = None,
    buffer_atr: float = 0.5,
) -> float:
    """
    Long : stop = (nearest confirmed swing low below entry_price within last
           `lookback` bars) - buffer_atr * ATR[decision_idx].
    Short: stop = (nearest confirmed swing high above entry_price within last
           `lookback` bars) + buffer_atr * ATR[decision_idx].

    "Nearest" = closest to entry_price in price space (the tightest valid
    structure that still invalidates the thesis).

    Caps & fallbacks:
      - If the structural stop is FARTHER than max_atr * ATR from entry
        (stop too wide): use stop = entry -+ max_atr * ATR (cap).
      - If no confirmed swing low/high below/above entry exists in the
        lookback window: use stop = entry -+ max_atr * ATR (ATR fallback).
      - If the resulting risk (|entry - stop|) < min_atr * ATR (stop too
        tight, e.g. a trivial wick): widen to entry -+ min_atr * ATR.
      - Risk must be > 0; if any degenerate case yields risk <= 0, return
        entry -+ min_atr * ATR.

    Returns: stop_price (float). Never None.
    """
```

### 1.3 `compute_natural_target`

```python
def compute_natural_target(
    df: pd.DataFrame,
    decision_idx: int,
    direction: str,
    entry_price: float,
    stop_price: float,
    min_rr: float = 1.5,
    lookback: int = 50,
    pivot_distance: int = PIVOT_DISTANCE,
    atr: pd.Series | None = None,
    atr_target_mult: float = 2.5,
) -> float | None:
    """
    Long : candidates = confirmed swing highs ABOVE entry_price within last
           `lookback` bars.
    Short: candidates = confirmed swing lows BELOW entry_price within last
           `lookback` bars.

    risk = |entry_price - stop_price|  (must be > 0; caller guarantees via stop fn)
    For each candidate level L, reward = |L - entry_price|, R = reward / risk.

    Selection:
      1. Filter candidates to those with R >= min_rr.
      2. Among filtered, pick the NEAREST overhead/below resistance
         (smallest |L - entry_price|) -> target.
      3. If filtered set is empty (no structural target offers min_rr):
         try ATR fallback target = entry +- atr_target_mult * ATR[decision_idx].
         If that gives R >= min_rr, return it.
      4. Else return None  -> caller MUST skip the signal (no valid target).

    Returns: target_price (float) or None.
    """
```

### 1.4 Orchestrator (recommended entry point for scanners)

```python
def compute_structure_trade(
    df: pd.DataFrame,
    signal_idx: int,
    direction: str,
    max_wait_bars: int = 5,
    min_rr: float = 1.5,
    max_atr: float = 2.0,
    atr: pd.Series | None = None,
    pivot_distance: int = PIVOT_DISTANCE,
    entry_fallback: str = "signal",
) -> dict | None:
    """
    Wires the three primitives in look-ahead-safe order:
      1. entry_price, entry_idx = compute_pullback_entry(...)   # may advance idx
      2. decision_idx = entry_idx
      3. stop_price  = compute_structure_stop(decision_idx=entry_idx, ...)
      4. target_price = compute_natural_target(decision_idx=entry_idx, ...)
      5. if target_price is None: return None  (skip — no valid R:R)
      6. sanity: risk = |entry - stop| > 0; final_rr = |target-entry|/risk
         if final_rr < min_rr: return None (defensive double-check)

    Returns dict:
      {entry_price, entry_idx, stop_price, target_price,
       risk, rr, entry_type: "pullback"|"market", decision_idx}
    or None if the trade should be skipped.
    """
```

**Design notes on the API refinement vs. the original spec:**

- The spec listed `compute_natural_target(df, signal_idx, direction, min_rr=1.5)` with no entry/stop. R-multiple is `reward / risk`, and risk requires a stop. I therefore added `entry_price` and `stop_price` as required params. This is unavoidable for a meaningful `min_rr` filter and is flagged here as an intentional, justified deviation.
- `compute_structure_stop` needs `entry_price` to (a) measure distance for the `max_atr` cap and (b) select the nearest swing below/above entry. Added as a required param.
- All three primitives take `decision_idx` (named `signal_idx` in the spec for entry/stop/target) rather than implicitly `signal_idx`, because pullback entries move the effective decision bar forward. The orchestrator always passes `entry_idx` for stop/target. Using `entry_idx` is strictly safer (more pivots confirmed) than `signal_idx`.
- `compute_pullback_entry` keeps the spec's `signal_idx` semantics (the bar the indicator fired) since the wait window is defined relative to the signal.

---

## 2. Algorithms (pseudocode + look-ahead verification)

### 2.0 Shared helpers

```
PIVOT_DISTANCE = 5

def _compute_atr(df, period=14):
    # Wilder ATR, identical to every scanner's _compute_atr.
    tr = max(high-low, |high-prev_close|, |low-prev_close|)  # per bar
    return tr.ewm(alpha=1/period, adjust=False).mean()

def _confirmed_pivots(df, as_of_idx, kind, pivot_distance=PIVOT_DISTANCE, lookback):
    # kind = "high" -> swing highs; "low" -> swing lows
    idxs, _ = find_peaks( (high if kind=="high" else -low), distance=pivot_distance )
    # CONFIRMED-ONLY filter: a pivot at p is knowable only at p + pivot_distance.
    confirmed = [p for p in idxs if p + pivot_distance <= as_of_idx]
    # lookback window: only pivots within [as_of_idx - lookback, as_of_idx]
    confirmed = [p for p in confirmed if as_of_idx - lookback <= p <= as_of_idx]
    return confirmed
```

**Look-ahead verification (US-114 lesson):** `find_peaks(distance=N)` requires N bars on each side with no higher/lower extreme. A peak at `p` is therefore unknowable until bar `p + N` has closed. The filter `p + pivot_distance <= as_of_idx` guarantees we never read a pivot that needed future bars to confirm. This is exactly the bug fixed in STR-S/T (entry at `c_idx + 1` instead of `c_idx + PIVOT_DISTANCE`); the module bakes the fix in centrally so scanners cannot reintroduce it.

### 2.1 `compute_pullback_entry`

```
def compute_pullback_entry(df, signal_idx, direction, max_wait_bars=5,
                           pivot_distance=5, ema_span=20, fallback="signal"):
    close_sig = close[signal_idx]
    atr_sig   = atr[signal_idx]            # for gap tolerance (optional)

    # --- Build candidate support levels, CONFIRMED at signal_idx (no look-ahead)
    levels = []
    if direction == "long":
        sl = _confirmed_pivots(df, signal_idx, "low", pivot_distance,
                              lookback=signal_idx)   # all confirmed lows to date
        for p in sl:
            lvl = low[p]
            if lvl < close_sig:                      # below current price
                levels.append(lvl)
        ema = close.ewm(span=ema_span, adjust=False).mean()
        ema_val = ema[signal_idx]
        if ema_val < close_sig and ema[signal_idx] > ema[signal_idx-1]:
            # rising EMA below price = dynamic support
            levels.append(ema_val)
        if not levels:
            return _fallback(df, signal_idx, max_wait_bars, fallback)
        support = max(levels)        # NEAREST below close (closest to price)
    else: # short — mirror
        sh = _confirmed_pivots(df, signal_idx, "high", ...)
        for p in sh:
            lvl = high[p]
            if lvl > close_sig: levels.append(lvl)
        ema_val = ema[signal_idx]
        if ema_val > close_sig and ema[signal_idx] < ema[signal_idx-1]:
            levels.append(ema_val)
        if not levels:
            return _fallback(...)
        support = min(levels)        # nearest above close

    # --- Wait for the pullback touch (limit order)
    n = len(df)
    for j in range(signal_idx + 1, min(signal_idx + max_wait_bars + 1, n)):
        if direction == "long":
            if open[j] <= support:
                return (open[j], j)              # gapped below limit -> fill open
            if low[j] <= support:
                return (support, j)              # touched limit -> fill limit
        else:
            if open[j] >= support:
                return (open[j], j)
            if high[j] >= support:
                return (support, j)

    # --- No touch within window -> market fallback
    return _fallback(df, signal_idx, max_wait_bars, fallback)

def _fallback(df, signal_idx, max_wait_bars, fallback):
    if fallback == "window_end":
        j = min(signal_idx + max_wait_bars, len(df)-1)
        return (close[j], j)
    return (close[signal_idx], signal_idx)     # default per spec
```

**Look-ahead verification:**
- The support LEVEL is built only from pivots confirmed at `signal_idx` (`p + PIVOT_DISTANCE <= signal_idx`) and the EMA value at `signal_idx` (EMA is causal: uses only past closes). No future data is read to *choose* the level.
- Reading `low[j] / high[j] / open[j]` for `j > signal_idx` is **not** look-ahead — it is the natural passage of time, modelled as a limit order resting on the book. At bar `j`'s close the touch is known; the fill is backdated to the limit price (standard limit-fill model). This is the same convention as every scanner's `_walk_forward_exit` which reads future `high/low` to test stop/target hits.
- We never use a support level that was only *discoverable* after `signal_idx` (e.g., a swing low that confirms at `signal_idx + 2`). That would be look-ahead and is forbidden by the confirmed-only filter applied at `signal_idx`.

**Realism note (flagged for the user):** `fallback="signal"` retroactively enters at `close[signal_idx]` after "waiting" `max_wait_bars`. The realistic interpretation is: *at signal time, place a limit at support AND a market order; if the limit fills, cancel the market; if not, you're already in at market at signal close.* If the user prefers strict sequential realism, `fallback="window_end"` enters at market at the end of the wait window. Default `"signal"` matches the spec; the option is exposed.

### 2.2 `compute_structure_stop`

```
def compute_structure_stop(df, decision_idx, direction, entry_price,
                            max_atr=2.0, min_atr=0.5, lookback=20,
                            pivot_distance=5, atr=None, buffer_atr=0.5):
    a = (atr if atr is not None else _compute_atr(df)).iloc[decision_idx]
    sign = +1 if direction == "long" else -1   # stop is on the opposite side

    # nearest confirmed swing on the invalidation side, within lookback
    if direction == "long":
        pivs = _confirmed_pivots(df, decision_idx, "low", pivot_distance, lookback)
        cand = [low[p] for p in pivs if low[p] < entry_price]
        # nearest below entry = the HIGHEST such low (closest to entry)
        struct_level = max(cand) if cand else None
    else:
        pivs = _confirmed_pivots(df, decision_idx, "high", pivot_distance, lookback)
        cand = [high[p] for p in pivs if high[p] > entry_price]
        struct_level = min(cand) if cand else None

    if struct_level is not None:
        stop = struct_level - sign * buffer_atr * a    # buffer into the structure
    else:
        stop = entry_price - sign * max_atr * a        # no structure -> ATR fallback

    # cap: if stop is wider than max_atr * ATR, tighten to the cap
    if abs(entry_price - stop) > max_atr * a:
        stop = entry_price - sign * max_atr * a
    # floor: if stop is tighter than min_atr * ATR, widen to the floor
    if abs(entry_price - stop) < min_atr * a:
        stop = entry_price - sign * min_atr * a
    if abs(entry_price - stop) <= 0:
        stop = entry_price - sign * min_atr * a
    return float(stop)
```

**Look-ahead verification:** pivots filtered by `p + PIVOT_DISTANCE <= decision_idx`; `decision_idx = entry_idx >= signal_idx`, so this is at least as strict as confirming at signal time. ATR uses `close.shift(1)` (causal). No future data read.

### 2.3 `compute_natural_target`

```
def compute_natural_target(df, decision_idx, direction, entry_price,
                            stop_price, min_rr=1.5, lookback=50,
                            pivot_distance=5, atr=None, atr_target_mult=2.5):
    a = (atr if atr is not None else _compute_atr(df)).iloc[decision_idx]
    risk = abs(entry_price - stop_price)
    if risk <= 0:
        return None
    if direction == "long":
        pivs = _confirmed_pivots(df, decision_idx, "high", pivot_distance, lookback)
        cand = [high[p] for p in pivs if high[p] > entry_price]
        # sort by distance above entry ascending (nearest overhead first)
        cand.sort(key=lambda L: L - entry_price)
        for L in cand:
            if (L - entry_price) / risk >= min_rr:
                return float(L)
        # no structural target meets min_rr -> ATR fallback
        atr_target = entry_price + atr_target_mult * a
    else:
        pivs = _confirmed_pivots(df, decision_idx, "low", pivot_distance, lookback)
        cand = [low[p] for p in pivs if low[p] < entry_price]
        cand.sort(key=lambda L: entry_price - L)
        for L in cand:
            if (entry_price - L) / risk >= min_rr:
                return float(L)
        atr_target = entry_price - atr_target_mult * a

    if abs(atr_target - entry_price) / risk >= min_rr:
        return float(atr_target)
    return None    # no valid target -> skip the trade
```

**Look-ahead verification:** identical pivot-confirmation guard. Targets only ever reference confirmed swing highs/lows or a causal ATR multiple. No future close is read to *select* the target.

---

## 3. Scanner Integration Plan

### 3.1 Classification (15 LIVE scanners; S/AH/AI are KILLED, out of scope)

| Group | Scanners | Action | Rationale |
|-------|----------|--------|-----------|
| **SWITCH (11)** | X (Parabolic SAR), Z (Stochastic), AA (Williams %R), AC (CCI), AD (Keltner), AE (4-week rule), AF (Candlestick, 2R), Y (ADX/DMI), W (Flags/Pennants), R (Alligator), B (MACD divergence) | Adopt `market_structure` module for entry/stop/target | All use `entry=close[signal_idx]`, fixed-ATR stops, fixed 3R/2R targets disconnected from structure |
| **KEEP (4)** | T (Head & Shoulders), U (Double Top/Bottom), V (Triangles), AG (Wedge) | No change — already derive target from pattern geometry / neckline / wedge height | Their targets ARE natural structure (pattern-measured). Forcing the module would discard pattern-specific R geometry. |

**Note for the coder:** The 4 KEEP scanners already use `find_peaks(distance=PIVOT_DISTANCE)` and start entry at `R_idx + PIVOT_DISTANCE` (STR-T) — the exact confirmed-pivot discipline this module centralizes. They are the gold-standard reference. Do not modify them in this US; if desired, a later US can route their *stop* through `compute_structure_stop` while keeping their pattern target.

The remaining older scanners (A–O, Q, P, AB, AJ, etc.) are NOT in the US-114 audited LIVE set and are out of scope for this US. They may adopt the module later under a separate US.

### 3.2 Modification pattern (before/after sketch)

The 11 SWITCH scanners share an identical shape in `scan()`:

**BEFORE (e.g. STR-X, STR-Y, STR-AE):**
```python
entry_price = close_arr[i]                       # buy the signal-bar close
stop_price  = entry_price - STOP_ATR_MULT * atr_arr[i]   # fixed ATR multiple
risk = entry_price - stop_price
if risk <= 0: continue
target_price = entry_price + risk * TARGET_RR    # fixed 3R
signals.append({"date": df.index[i], "ticker": ticker, ...,
                "entry_price": entry_price, "stop_price": stop_price,
                "target_price": target_price, ...})
```

**AFTER:**
```python
from market_structure import compute_structure_trade   # sibling import

# ... inside the signal-detection loop, when a long signal is confirmed at bar i:
trade = compute_structure_trade(
    df, signal_idx=i, direction="long",
    max_wait_bars=5, min_rr=1.5, max_atr=2.0,
    atr=atr,                       # reuse the scanner's already-computed ATR
    entry_fallback="signal",
)
if trade is None:
    continue                        # no valid target -> skip this signal
signals.append({
    "date": df.index[i],            # SIGNAL date (kept for auditability)
    "entry_date": df.index[trade["entry_idx"]],   # NEW: actual entry bar
    "entry_idx":  trade["entry_idx"],            # NEW: positional, for run_backtest
    "ticker": ticker,
    "strategy_id": STRATEGY_ID, "strategy_name": STRATEGY_NAME,
    "strategy_version": STRATEGY_VERSION,        # bump to "2.0" (structure-based)
    "direction": "long",
    "entry_price": round(trade["entry_price"], 4),
    "stop_price":   round(trade["stop_price"], 4),
    "target_price": round(trade["target_price"], 4),
    "risk":   round(trade["risk"], 4),
    "rr":     round(trade["rr"], 3),
    "entry_type": trade["entry_type"],           # "pullback" | "market"
    "signal_type": "psar_flip_long",             # scanner-specific, keep
})
```

**Key integration changes (these are REQUIRED, not optional):**

1. **`entry_idx` must propagate into the signal dict.** The scanner's `run_backtest()` currently derives `entry_idx` from `sig["date"]` (the signal bar). For pullback trades `entry_idx > signal_idx`, so the exit walk MUST start at `entry_idx`, not `signal_idx`. Concretely, `run_backtest` becomes:
   ```python
   entry_idx = sig.get("entry_idx")
   if entry_idx is None:
       entry_idx = df.index.get_loc(sig["date"])   # legacy fallback
   exit_result = _walk_forward_exit(df, entry_idx, sig["direction"],
                                    sig["entry_price"], sig["stop_price"],
                                    sig["target_price"])
   ```
2. **`_walk_forward_exit` is unchanged in logic** — it already starts at `entry_idx + 1` and counts `MAX_HOLD_BARS` from there. The only requirement is that callers pass the correct `entry_idx`. Hold-time semantics: bars in trade are counted from the actual entry bar, not the signal bar. This is the realistic interpretation (you're not "in" the trade during the pullback wait).
3. **Variable R on target exits.** Because targets are no longer a fixed multiple, `_walk_forward_exit` must compute `r_multiple` for target exits dynamically (STR-T already does this — `r_multiple=None` then recomputed in `run_backtest`). The 11 SWITCH scanners currently hardcode `r_multiple: TARGET_RR` on target hits; this MUST change to dynamic computation:
   ```python
   risk = entry_price - stop_price if direction=="long" else stop_price - entry_price
   gain = (exit_price - entry_price) if direction=="long" else (entry_price - exit_price)
   r_multiple = round(gain / risk, 3) if risk > 0 else 0.0
   ```
   (STR-AF with `TARGET_RR=2.0` has the same hardcoded-R bug and gets the same fix.)
4. **Version bump.** Each modified scanner's `STRATEGY_VERSION` goes to `"2.0"` and `__doc__` is updated to describe structure-based entry/stop/target. This preserves auditability: results tagged v1.x are the old fixed-3R behaviour, v2.x is structure-based.
5. **Module import path.** The module lives in the same directory as the scanners (`scanners/market_structure.py`), so a plain `from market_structure import compute_structure_trade` works when scanners are run from that directory (the existing `run_phase1a` entry points and the orchestrator already execute from there). The coder must verify import works both for `python scanner_x.py --backtest` and for orchestrator-driven invocation; if needed, add a `sys.path.insert(0, os.path.dirname(__file__))` guard inside each scanner (STR-R already uses `sys.path.insert`).

### 3.3 Per-scanner integration notes

- **STR-AE (4-week rule):** Currently uses the opposite Donchian boundary as stop and 3R target. Under the new module, the breakout signal still fires the same way, but entry becomes a pullback to the nearest confirmed support below the breakout close, stop goes below that support (capped at 2 ATR), and target is the next confirmed overhead resistance with R >= 1.5. The Donchian channel remains the *signal trigger only*.
- **STR-X (Parabolic SAR):** The SAR flip is the trigger; the SAR value is no longer the stop. Stop = structure below the pullback entry. `psar` is kept in the dict for diagnostics.
- **STR-AF (Candlestick, currently 2R):** The candlestick pattern is the trigger; the `TARGET_RR=2.0` constant is removed entirely. Pattern-detection logic is untouched.
- **STR-B (MACD divergence):** Already uses `lowest low in prior 20 bars` as a target heuristic — this is a crude structure target. Under the module it is replaced by `compute_natural_target` (nearest confirmed overhead resistance meeting min_rr). Net effect: tighter, more realistic targets.
- **STR-W (Flags/Pennants):** Flag/pennant is the trigger. Pattern pole height is currently used for target in some variants; if W already uses pattern-measured targets it should arguably move to KEEP — **the coder must inspect W and reclassify it to KEEP if its target is pattern-derived (pole height), matching AG.** Flagged here as a classification check, not a decision.

---

## 4. Look-Ahead Bias Prevention (centralised)

This US exists because US-114 found 7 look-ahead scanners. The module must make that class of bug *structurally impossible* for the 11 SWITCH scanners. The guards:

1. **Single pivot primitive.** All swing detection goes through `_confirmed_pivots(as_of_idx, ...)` which enforces `p + PIVOT_DISTANCE <= as_of_idx`. Scanners no longer call `find_peaks` directly, so they cannot reintroduce the `entry at pivot + 1` bug.
2. **`decision_idx` discipline.** Stop and target are computed at `entry_idx` (the actual fill bar), never at `signal_idx`, for pullback trades. This is stricter (more pivots confirmed) and avoids using structure that was only confirmable after the signal but before the entry.
3. **Support levels for pullback are frozen at `signal_idx`.** The limit-order level is chosen from pivots confirmed *at signal time*. We do not let a pullback "discover" a support that only confirmed during the wait window — that would be look-ahead (you'd be placing a limit order at a level you couldn't have known existed at signal time). The wait window only *tests* a pre-selected level.
4. **Limit-fill model is causal.** Reading `low[j]/high[j]` for `j > signal_idx` models a resting limit order and is the same convention as the existing `_walk_forward_exit`. It is not look-ahead.
5. **No future close is used to *select* entry/stop/target.** Future bars are used only to (a) test whether a resting limit order fills and (b) test stop/target hits in the exit walk — both standard, causal backtest operations.
6. **ATR is causal** (`close.shift(1)` Wilder smoothing). EMA is causal. Neither reads future data.
7. **Codified assertion (recommended for the module):** at the top of each primitive, assert every pivot used satisfies `p + pivot_distance <= decision_idx`. A debug-mode assertion (`if __debug__` or an env flag) makes regressions loud during testing without costing runtime in production.

---

## 5. Backtesting Considerations

The pullback entry changes the entry bar, which propagates into several backtest mechanics. The coder MUST handle all of these:

### 5.1 R-multiple is now per-trade variable
With structure targets, target R is no longer a constant 3.0/2.0. Every R-multiple (for target, time, and stop exits) must be computed from actual `{entry, stop, exit}` prices. Stop exits are still −1.0R by construction (`exit_price = stop_price`). Target exits range widely (e.g., 1.6R, 2.3R, 4.1R). Time exits use the dynamic formula. The summary printers (`_print_summary`) already aggregate `r_multiple` generically, so they need no change — but any code that *assumes* `r_multiple == TARGET_RR` on target hits must be removed (STR-AE/X/Y/Z/AA/AC/AD/AF all have this assumption baked into `_walk_forward_exit`).

### 5.2 The exit walk starts at `entry_idx`, not `signal_idx`
For pullback trades, `entry_idx = signal_idx + k` (k up to `max_wait_bars`). If the exit walk mistakenly starts at `signal_idx`, it would simulate stop/target hits during the pullback window using an entry price that wasn't filled yet — a logical error and a subtle look-ahead (you'd be trading before you're in the trade). The fix is §3.2 change #1: propagate `entry_idx` and use it.

### 5.3 `MAX_HOLD_BARS` countdown
Hold time is counted from `entry_idx + 1`. A scanner with `MAX_HOLD_BARS=20` now holds up to 20 bars *after the pullback fill*, not after the signal. This slightly lengthens total trade duration (signal → up to 5 wait bars → up to 20 hold bars). Acceptable and realistic. No code change needed beyond using the correct `entry_idx`.

### 5.4 Signal overlap / cooldown (IMPORTANT, magnified by pullback)
Pullback entries delay the actual entry by up to `max_wait_bars`. This creates a new overlap risk: a signal at bar `i` enters at `i+4`, while a second signal at `i+2` enters at `i+3` — two live trades on the same ticker. The existing scanners do not enforce a per-ticker cooldown (they rely on signal sparsity). The coder must add a **cooldown guard** at the scanner level: after a signal is accepted (i.e., `compute_structure_trade` returns non-None), skip all subsequent signals on that ticker until the trade's exit is resolved (or for a fixed `cooldown_bars`, suggested 20). This should be a small shared helper, e.g. `last_trade_end_idx` tracking, inside each scanner's `scan()` loop. Flagged as REQUIRED for the SWITCH scanners; without it, trade counts inflate and R-distributions double-count overlapping exposure.

### 5.5 Trade-count expectation
Structure-based filtering (min_rr skip + pullback) will reduce signal count relative to v1.x. Expect 20–50% fewer trades per scanner. This is expected and desirable (we are filtering out trades with no realistic target and replacing "buy the high" entries with pullback entries). The validation harness must compare v1.x vs v2.x on win-rate, avg R, profit factor, AND trade count — a sharp drop in trades with flat avg R is not necessarily an improvement (could mean we're only keeping easy wins). The risk-guardian should review this in validation.

### 5.6 Determinism
`compute_structure_trade` is deterministic given `df` and params. No randomness. Backtests are reproducible.

---

## 6. Risk Considerations

### 6.1 min_rr filter (trade rejection)
`min_rr=1.5` is the floor. Trades with no overhead resistance offering 1.5R (and no ATR fallback meeting 1.5R) are SKIPPED. This is the primary safety mechanism: we do not take trades with no realistic reward. The risk-guardian should confirm 1.5 is appropriate per ADR-001 tier; if a scanner targets shorter horizons (e.g., STR-AF candlestick, 8-bar holds), a lower `min_rr=1.2` may be warranted — exposed as a per-scanner param, NOT a global change. Default 1.5.

### 6.2 Max stop distance (`max_atr=2.0`)
Stops are capped at 2.0 × ATR from entry. This prevents a deep structural swing low (e.g., a major higher-timeframe low 6 ATR below entry) from producing an untradable 6R-risk stop. When the structural stop exceeds the cap, the cap is used. This bounds per-trade risk regardless of structure. Aligned with the SOUL.md 1%-of-capital discipline: the *scanner* returns price levels; the *position sizer* (out of scope here) converts `risk` into share size. The module must surface `risk` in the trade dict (it does: `risk` field) so the sizer can enforce the 1% rule.

### 6.3 Min stop distance (`min_atr=0.5`)
Prevents a trivial wick 0.1 ATR below entry from producing a stop so tight it gets clipped by noise. Floor at 0.5 × ATR.

### 6.4 No valid target → skip
`compute_natural_target` returns `None` → the orchestrator returns `None` → the scanner `continue`s. No trade is taken. This is correct: a long with no overhead resistance and an ATR fallback that doesn't clear min_rr is not a trade worth taking.

### 6.5 Degenerate risk
If `entry == stop` (risk ≤ 0) after all caps/floors, the orchestrator returns `None`. Stops the scanner from emitting a zero-risk trade that would produce infinite R.

### 6.6 Pullback can move against you before entry
During the `max_wait_bars` wait, price can fall through the support without filling the limit at the level (gap below, filled at open — handled), or keep falling (in which case the limit fills at support and the stop, just below that support, may be hit very soon — a realistic losing trade). This is the real risk of pullback entries and is correctly simulated: the exit walk starts at `entry_idx` and will catch the immediate stop-out. The backtest will reflect these losses; this is a feature, not a bug.

### 6.7 What this module does NOT do (out of scope, by SOUL.md rules)
- It does not size positions or touch capital. It returns price levels only.
- It does not execute trades or interact with any exchange/account.
- It does not choose leverage.
- It does not modify live-system settings.
The coder must not add any execution, sizing, or API code to this module.

---

## 7. Testing Plan

The module must be testable in isolation (per spec). All tests live in `~/HermesForge/scripts/validation/scanners/test_market_structure.py` and run with `python -m pytest test_market_structure.py` (or plain `python test_market_structure.py` if pytest is unavailable — keep it stdlib-runnable).

### 7.1 Synthetic-data unit tests
Build small hand-crafted DataFrames with known pivots, supports, and pullbacks. Each test asserts exact numeric outcomes.

- **T1 — confirmed-pivot guard:** a swing low at bar 10, `PIVOT_DISTANCE=5`. Assert `_confirmed_pivots(as_of_idx=14)` excludes it, `_confirmed_pivots(as_of_idx=15)` includes it. (Direct encoding of the US-114 lesson.)
- **T2 — compute_structure_stop, long, normal:** entry=100, a confirmed swing low at 95, ATR=2 → stop = 95 − 0.5×2 = 94.
- **T3 — compute_structure_stop, cap:** entry=100, nearest confirmed swing low at 80 (5 ATR below with ATR=4), `max_atr=2.0` → stop = 100 − 2.0×4 = 92 (cap applied, not 80−buffer).
- **T4 — compute_structure_stop, no structure:** no confirmed swing low below entry → stop = entry − max_atr×ATR.
- **T5 — compute_structure_stop, floor:** swing low at 99.5, ATR=2, `min_atr=0.5` → stop = 100 − 1.0 = 99 (floor applied, not 99.5−1.0=98.5? assert floor logic precisely).
- **T6 — compute_natural_target, long, meets min_rr:** entry=100, stop=95 (risk=5), confirmed swing high at 108 (R=1.6 ≥ 1.5) → target=108.
- **T7 — compute_natural_target, nearest too close, next qualifies:** swing highs at 102 (R=0.4) and 110 (R=2.0) → target=110 (skip the too-close 102, take nearest that meets min_rr).
- **T8 — compute_natural_target, no structure → ATR fallback:** no confirmed swing high above entry, ATR=4, `atr_target_mult=2.5` → target=110 if R≥1.5.
- **T9 — compute_natural_target, ATR fallback fails min_rr → None:** risk=10, ATR=2 → ATR target=5 → R=0.5 < 1.5 → None.
- **T10 — compute_pullback_entry, long, touch:** support=95, bar signal+3 has low=94 → entry=95, entry_idx=signal+3.
- **T11 — compute_pullback_entry, gap fill:** bar opens at 93 (below 95) → entry=93 (fill at open).
- **T12 — compute_pullback_entry, no touch, fallback=signal:** → (close[signal], signal).
- **T13 — compute_pullback_entry, no touch, fallback=window_end:** → (close[signal+5], signal+5).
- **T14 — compute_structure_trade, full happy path:** assert returns dict with all keys and `entry_type="pullback"`.
- **T15 — compute_structure_trade, target None → returns None.**

### 7.2 Look-ahead regression tests (the critical suite)
- **L1 — future-bar invariance:** build a 200-bar series. Compute `compute_structure_trade(df, signal_idx=100, ...)`. Then *append* 50 synthetic future bars (after signal) that drastically change pivots beyond the lookback window. Re-run with `signal_idx=100` on the extended df. Assert outputs IDENTICAL (the decision at bar 100 cannot depend on bars > 100 + max_wait_bars for the entry, and not at all on far-future structure for stop/target). This is the definitive look-ahead test.
- **L2 — pivot-confirmation invariance:** mutate bars between `pivot` and `pivot + PIVOT_DISTANCE` so the pivot would no longer qualify; assert the pivot is NOT used when `decision_idx < pivot + PIVOT_DISTANCE`.
- **L3 — pullback level frozen at signal:** modify a bar at `signal_idx + 2` to create a *new* swing low that confirms at `signal_idx + 2 + PIVOT_DISTANCE` (which is > signal_idx). Assert this new low is NOT used as the pullback support for the signal at `signal_idx` (it wasn't confirmed at signal time).

### 7.3 Property/invariant tests
- **P1:** for every pivot `p` referenced by any function output, assert `p + PIVOT_DISTANCE <= decision_idx` used.
- **P2:** `compute_structure_stop` always returns a stop on the correct side (stop < entry for long; stop > entry for short) and `risk > 0`.
- **P3:** `compute_natural_target` returns `None` or a target on the correct side with R ≥ min_rr (when not None).

### 7.4 Integration / regression tests (per SWITCH scanner)
- **I1 — smoke:** run each modified scanner's `run_backtest` on one cached parquet (e.g., SPY) and assert it returns a non-empty list of trades with valid `entry_idx`, `entry_price`, `stop_price`, `target_price`, and `r_multiple` fields.
- **I2 — no hardcoded R:** assert no target-exit trade has `r_multiple` exactly equal to the old `TARGET_RR` constant for scanners where target R is now variable (allow for coincidental equality but check the distribution has variance).
- **I3 — entry_idx consistency:** assert `entry_idx` in every signal dict and that `run_backtest`'s exit walk starts at `entry_idx` (spot-check by asserting `bars_held >= 1` and the first exit-test bar is `entry_idx + 1`).
- **I4 — before/after comparison:** for each SWITCH scanner, save v1.x results CSV and v2.x results CSV; the risk-guardian reviews delta in trade count, win rate, avg R, profit factor. A v2.x that keeps win rate but halves trade count with no avg-R improvement is a yellow flag.

### 7.5 Acceptance gate (before any scanner goes back to LIVE)
- All 7.1 + 7.2 + 7.3 tests pass.
- All 11 SWITCH scanners pass 7.4.
- Risk-guardian reviews the v1.x→v2.x delta and signs off (ADR-001).
- No scanner is marked LIVE until the swarm (architect/coder/researcher/risk-guardian/backtester) re-validates per the US-114 protocol.

---

## 8. Deliverables Checklist (for the coder)

- [ ] `~/HermesForge/scripts/validation/scanners/market_structure.py` with the 3 primitives + orchestrator + `_confirmed_pivots` + shared `_compute_atr`.
- [ ] `~/HermesForge/scripts/validation/scanners/test_market_structure.py` covering T1–T15, L1–L3, P1–P3.
- [ ] Modify the 11 SWITCH scanners (X, Z, AA, AC, AD, AE, AF, Y, W, R, B): import module, replace entry/stop/target block with `compute_structure_trade`, propagate `entry_idx`, make target-R dynamic, bump version to 2.0, add cooldown guard, update docstrings.
- [ ] Re-classify STR-W after inspecting whether its target is pattern-derived (pole height) — if so, move W to KEEP and do not modify.
- [ ] Leave the 4 KEEP scanners (T, U, V, AG) untouched.
- [ ] Commit each change to git immediately (user hard rule: no uncommitted changes left in the working tree).
- [ ] Run the full test suite + one-symbol backtest per scanner; attach output to the coder report.

---

## 9. Open Questions for the User / Risk-Guardian

1. **`min_rr` per scanner:** default 1.5 globally, or 1.2 for short-horizon scanners (STR-AF 8-bar holds)? Recommend: default 1.5, let risk-guardian tune per scanner after seeing v2.x deltas.
2. **`fallback` semantics:** `"signal"` (spec default, retroactive market entry at signal close) vs `"window_end"` (market entry at end of wait window). Recommend `"signal"` to match spec; flag for user.
3. **Cooldown:** enforce a 20-bar per-ticker cooldown after each accepted signal? Recommend yes (§5.4). Confirm with user.
4. **STR-W classification:** KEEP or SWITCH? Coder to inspect and decide; default SWITCH unless target is pattern-derived.
5. **Apply to KEEP scanners' stops later?** Out of scope here; possible future US to route T/U/V/AG stops through `compute_structure_stop` while keeping their pattern targets.

---

**End of design.** Implementation is delegated to the coder (ADR-001 T2 floor). This document is design-only; no code has been written.
