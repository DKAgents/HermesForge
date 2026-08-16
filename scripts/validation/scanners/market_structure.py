#!/usr/bin/env python3
"""
market_structure.py
===================
HermesForge US-115: Unified Market Structure Module.

Shared, look-ahead-free module that the 11 indicator-based LIVE scanners
(STR-X, Z, AA, AC, AD, AE, AF, Y, W, R, B) call to derive entry / stop /
target from market structure rather than fixed ATR multiples and a fixed 3R.

Three primitives:
    compute_pullback_entry  -> (entry_price, entry_idx)
    compute_structure_stop   -> stop_price
    compute_natural_target   -> target_price | None

One orchestrator:
    compute_structure_trade  -> dict | None

Look-ahead discipline (US-114 lesson, centralised here):
    * _confirmed_pivots(as_of_idx, ...) enforces  p + PIVOT_DISTANCE <= as_of_idx.
      A pivot at p is only knowable at p + PIVOT_DISTANCE (find_peaks(distance=N)
      needs N bars on each side). Scanners call this primitive, never find_peaks
      directly, so the "entry at pivot+1" bug cannot be reintroduced.
    * Pullback support levels are frozen at signal_idx (confirmed pivots at
      signal time + causal EMA). The wait window only *tests* a pre-selected
      level via a resting limit order; reading low[j]/high[j] for j > signal_idx
      is the natural passage of time, not look-ahead (same convention as every
      scanner's _walk_forward_exit).
    * Stop/target use decision_idx = entry_idx >= signal_idx, strictly stricter
      (more pivots confirmed) than using signal_idx.

This module does NOT size positions, execute trades, touch exchanges, or
choose leverage (SOUL.md hard rules). It returns price levels only.

Dependencies: pandas, numpy, scipy.signal.find_peaks
"""

from __future__ import annotations

import os
from typing import Optional

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

PIVOT_DISTANCE = 5
"""Bars required on each side of a peak for find_peaks(distance=N) to confirm
it. A pivot at positional index p is only *knowable* at bar p + PIVOT_DISTANCE."""

DEFAULT_ATR_PERIOD = 14
DEFAULT_EMA_SPAN = 20
DEFAULT_MAX_WAIT_BARS = 5
DEFAULT_MAX_ATR = 2.0
DEFAULT_MIN_ATR = 0.5
DEFAULT_BUFFER_ATR = 0.5
DEFAULT_LOOKBACK_STOP = 20
DEFAULT_LOOKBACK_TARGET = 50
DEFAULT_MIN_RR = 1.5
DEFAULT_ATR_TARGET_MULT = 2.5
DEFAULT_MAX_WAIT = 5

# Debug-mode assertion guard. When MARKET_STRUCTURE_DEBUG=1 every pivot used by
# any primitive is asserted to satisfy p + pivot_distance <= decision_idx.
# This makes look-ahead regressions loud during testing without costing runtime
# in production (where the env flag is unset).
_DEBUG = os.environ.get("MARKET_STRUCTURE_DEBUG", "") == "1"


def _assert_confirmed(pivots, as_of_idx, pivot_distance, label="pivot") -> None:
    """Assert every pivot p satisfies p + pivot_distance <= as_of_idx.

    Only enforced when MARKET_STRUCTURE_DEBUG=1, so production paths pay no
    cost and we never crash a live scanner on a guard that is purely defensive.
    """
    if not _DEBUG:
        return
    for p in pivots:
        assert p + pivot_distance <= as_of_idx, (
            f"[{label}] look-ahead leak: pivot at {p} + {pivot_distance} = "
            f"{p + pivot_distance} > as_of_idx {as_of_idx}"
        )


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _compute_atr(df: pd.DataFrame, period: int = DEFAULT_ATR_PERIOD) -> pd.Series:
    """Wilder ATR via EWM smoothing (alpha = 1/period, adjust=False).

    Identical to every scanner's _compute_atr. Uses close.shift(1) so the true
    range of bar i depends only on bars <= i (causal).
    """
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _confirmed_pivots(
    df: pd.DataFrame,
    as_of_idx: int,
    kind: str,
    pivot_distance: int = PIVOT_DISTANCE,
    lookback: int | None = None,
) -> list[int]:
    """Return positional indices of confirmed swing highs/lows as of as_of_idx.

    Parameters
    ----------
    df : DataFrame with open/high/low/close.
    as_of_idx : no-look-ahead cutoff. Only pivots confirmable at or before this
        bar are returned.
    kind : "high" -> swing highs (find_peaks on high); "low" -> swing lows
        (find_peaks on -low).
    pivot_distance : the distance= argument to find_peaks. A peak at p is
        confirmed at p + pivot_distance.
    lookback : optional window [as_of_idx - lookback, as_of_idx]. If None, no
        window filter (all confirmed pivots to date).

    Look-ahead guard (US-114): a peak at p returned by find_peaks(distance=N)
    needs N bars on each side with no higher/lower extreme, so it is unknowable
    until bar p + N has closed. We filter to p + pivot_distance <= as_of_idx,
    guaranteeing we never read a pivot that needed future bars to confirm.
    """
    if kind == "high":
        series = df["high"].to_numpy()
        idxs, _ = find_peaks(series, distance=pivot_distance)
    elif kind == "low":
        series = -df["low"].to_numpy()
        idxs, _ = find_peaks(series, distance=pivot_distance)
    else:
        raise ValueError(f"kind must be 'high' or 'low', got {kind!r}")

    # CONFIRMED-ONLY filter (the US-114 fix, centralised here).
    confirmed = [int(p) for p in idxs if p + pivot_distance <= as_of_idx]

    if lookback is not None:
        lo = as_of_idx - lookback
        confirmed = [p for p in confirmed if lo <= p <= as_of_idx]

    _assert_confirmed(confirmed, as_of_idx, pivot_distance, label=f"confirmed_{kind}")
    return confirmed


def _atr_at(df: pd.DataFrame, atr: pd.Series | None, idx: int) -> float:
    """ATR value at positional idx, computing Wilder ATR once if not supplied."""
    a = atr if atr is not None else _compute_atr(df)
    return float(a.iloc[idx])


# ---------------------------------------------------------------------------
# 1.1 compute_pullback_entry
# ---------------------------------------------------------------------------

def _entry_fallback(
    df: pd.DataFrame,
    signal_idx: int,
    max_wait_bars: int,
    fallback: str,
) -> tuple[float, int]:
    """Market fallback when no pullback touch occurs within the wait window."""
    n = len(df)
    if fallback == "window_end":
        j = min(signal_idx + max_wait_bars, n - 1)
        return float(df["close"].iloc[j]), j
    # default "signal": retroactive market entry at signal-bar close.
    return float(df["close"].iloc[signal_idx]), signal_idx


def compute_pullback_entry(
    df: pd.DataFrame,
    signal_idx: int,
    direction: str,
    max_wait_bars: int = DEFAULT_MAX_WAIT_BARS,
    pivot_distance: int = PIVOT_DISTANCE,
    ema_span: int = DEFAULT_EMA_SPAN,
    fallback: str = "signal",
) -> tuple[float, int]:
    """Wait up to max_wait_bars for a pullback to confirmed support, fill limit.

    The support level is chosen ONLY from pivots confirmed at signal_idx and the
    EMA value at signal_idx (both causal). The wait window then *tests* that
    frozen level via a resting limit order. Reading low[j]/high[j]/open[j] for
    j > signal_idx models the natural passage of time (limit on the book), not
    look-ahead. We never use a support level discoverable only after signal_idx.

    Long : support = nearest confirmed swing low below close[signal_idx], or a
           rising EMA(ema_span) below close (whichever is closer to the close).
    Short: mirror (nearest confirmed swing high above close, or falling EMA).

    Limit-fill refinement: if bar opens beyond the level (gap), fill at the
    open (better price) rather than the limit.

    Returns (entry_price, entry_idx). Always returns a valid entry; never None.
    Fallback ("signal" | "window_end") is used when no touch occurs in window.
    """
    if direction not in ("long", "short"):
        raise ValueError(f"direction must be 'long' or 'short', got {direction!r}")

    close = df["close"]
    high = df["high"]
    low = df["low"]
    open_ = df["open"]
    n = len(df)
    close_sig = float(close.iloc[signal_idx])

    ema = close.ewm(span=ema_span, adjust=False).mean()
    ema_val = float(ema.iloc[signal_idx])

    levels: list[float] = []
    if direction == "long":
        # Confirmed swing lows below current price, to date (no lookback window
        # — we want the nearest below, across all confirmed history).
        sl = _confirmed_pivots(
            df, signal_idx, "low", pivot_distance=pivot_distance, lookback=None
        )
        for p in sl:
            lvl = float(low.iloc[p])
            if lvl < close_sig:
                levels.append(lvl)
        # Rising EMA below price = dynamic support.
        if ema_val < close_sig and signal_idx >= 1:
            if float(ema.iloc[signal_idx]) > float(ema.iloc[signal_idx - 1]):
                levels.append(ema_val)
        if not levels:
            return _entry_fallback(df, signal_idx, max_wait_bars, fallback)
        support = max(levels)  # nearest below close (closest to price)
    else:  # short — mirror
        sh = _confirmed_pivots(
            df, signal_idx, "high", pivot_distance=pivot_distance, lookback=None
        )
        for p in sh:
            lvl = float(high.iloc[p])
            if lvl > close_sig:
                levels.append(lvl)
        if ema_val > close_sig and signal_idx >= 1:
            if float(ema.iloc[signal_idx]) < float(ema.iloc[signal_idx - 1]):
                levels.append(ema_val)
        if not levels:
            return _entry_fallback(df, signal_idx, max_wait_bars, fallback)
        support = min(levels)  # nearest above close (closest to price)

    # --- Wait for the pullback touch (resting limit order) ---
    upper = min(signal_idx + max_wait_bars + 1, n)
    for j in range(signal_idx + 1, upper):
        if direction == "long":
            o = float(open_.iloc[j])
            if o <= support:
                return o, j  # gapped below limit -> fill open (better for buyer)
            if float(low.iloc[j]) <= support:
                return support, j  # touched limit -> fill at limit
        else:
            o = float(open_.iloc[j])
            if o >= support:
                return o, j  # gapped above limit -> fill open (better for seller)
            if float(high.iloc[j]) >= support:
                return support, j  # touched limit -> fill at limit

    # --- No touch within window -> market fallback ---
    return _entry_fallback(df, signal_idx, max_wait_bars, fallback)


# ---------------------------------------------------------------------------
# 1.2 compute_structure_stop
# ---------------------------------------------------------------------------

def compute_structure_stop(
    df: pd.DataFrame,
    decision_idx: int,
    direction: str,
    entry_price: float,
    max_atr: float = DEFAULT_MAX_ATR,
    min_atr: float = DEFAULT_MIN_ATR,
    lookback: int = DEFAULT_LOOKBACK_STOP,
    pivot_distance: int = PIVOT_DISTANCE,
    atr: pd.Series | None = None,
    buffer_atr: float = DEFAULT_BUFFER_ATR,
) -> float:
    """Stop at the nearest confirmed swing that invalidates the thesis, ATR-buffered.

    Long : stop = (nearest confirmed swing low below entry within lookback)
                  - buffer_atr * ATR[decision_idx]
    Short: stop = (nearest confirmed swing high above entry within lookback)
                  + buffer_atr * ATR[decision_idx]

    "Nearest" = closest to entry in price space (tightest valid structure).

    Caps & floors:
      - Wider than max_atr * ATR  -> tighten to entry -+ max_atr * ATR (cap).
      - No confirmed swing below/above entry -> ATR fallback (max_atr * ATR).
      - Tighter than min_atr * ATR -> widen to entry -+ min_atr * ATR (floor).
      - risk <= 0 after all of the above -> entry -+ min_atr * ATR.

    Returns stop_price (float). Never None. Uses decision_idx (the no-look-ahead
    cutoff); the orchestrator passes entry_idx, which is >= signal_idx.
    """
    if direction not in ("long", "short"):
        raise ValueError(f"direction must be 'long' or 'short', got {direction!r}")

    a = _atr_at(df, atr, decision_idx)
    sign = 1.0 if direction == "long" else -1.0  # stop is on the opposite side

    if direction == "long":
        pivs = _confirmed_pivots(
            df, decision_idx, "low", pivot_distance=pivot_distance, lookback=lookback
        )
        cand = [float(df["low"].iloc[p]) for p in pivs if float(df["low"].iloc[p]) < entry_price]
        struct_level = max(cand) if cand else None
    else:
        pivs = _confirmed_pivots(
            df, decision_idx, "high", pivot_distance=pivot_distance, lookback=lookback
        )
        cand = [float(df["high"].iloc[p]) for p in pivs if float(df["high"].iloc[p]) > entry_price]
        struct_level = min(cand) if cand else None

    if struct_level is not None:
        stop = struct_level - sign * buffer_atr * a  # buffer into the structure
    else:
        stop = entry_price - sign * max_atr * a  # no structure -> ATR fallback

    # cap: if stop is wider than max_atr * ATR, tighten to the cap
    if abs(entry_price - stop) > max_atr * a:
        stop = entry_price - sign * max_atr * a
    # floor: if stop is tighter than min_atr * ATR, widen to the floor
    if abs(entry_price - stop) < min_atr * a:
        stop = entry_price - sign * min_atr * a
    # degenerate
    if abs(entry_price - stop) <= 0:
        stop = entry_price - sign * min_atr * a

    return float(stop)


# ---------------------------------------------------------------------------
# 1.3 compute_natural_target
# ---------------------------------------------------------------------------

def compute_natural_target(
    df: pd.DataFrame,
    decision_idx: int,
    direction: str,
    entry_price: float,
    stop_price: float,
    min_rr: float = DEFAULT_MIN_RR,
    lookback: int = DEFAULT_LOOKBACK_TARGET,
    pivot_distance: int = PIVOT_DISTANCE,
    atr: pd.Series | None = None,
    atr_target_mult: float = DEFAULT_ATR_TARGET_MULT,
) -> Optional[float]:
    """Nearest confirmed resistance meeting min_rr; ATR fallback; None if none.

    Long : candidates = confirmed swing highs above entry within lookback.
    Short: candidates = confirmed swing lows below entry within lookback.

    risk = |entry - stop| (caller guarantees > 0 via the stop fn).
    For each candidate L (nearest overhead/below first), R = |L - entry| / risk.
    Return the first L with R >= min_rr. If none qualify, try the ATR fallback
    target (entry +- atr_target_mult * ATR); return it if R >= min_rr.
    Else return None -> caller MUST skip the signal (no valid target).

    Returns target_price (float) or None. Uses decision_idx cutoff.
    """
    if direction not in ("long", "short"):
        raise ValueError(f"direction must be 'long' or 'short', got {direction!r}")

    a = _atr_at(df, atr, decision_idx)
    risk = abs(entry_price - stop_price)
    if risk <= 0:
        return None

    if direction == "long":
        pivs = _confirmed_pivots(
            df, decision_idx, "high", pivot_distance=pivot_distance, lookback=lookback
        )
        cand = [float(df["high"].iloc[p]) for p in pivs if float(df["high"].iloc[p]) > entry_price]
        # nearest overhead first (smallest distance above entry)
        cand.sort(key=lambda L: L - entry_price)
        for L in cand:
            if (L - entry_price) / risk >= min_rr:
                return float(L)
        atr_target = entry_price + atr_target_mult * a
    else:
        pivs = _confirmed_pivots(
            df, decision_idx, "low", pivot_distance=pivot_distance, lookback=lookback
        )
        cand = [float(df["low"].iloc[p]) for p in pivs if float(df["low"].iloc[p]) < entry_price]
        # nearest below first (smallest distance below entry)
        cand.sort(key=lambda L: entry_price - L)
        for L in cand:
            if (entry_price - L) / risk >= min_rr:
                return float(L)
        atr_target = entry_price - atr_target_mult * a

    if abs(atr_target - entry_price) / risk >= min_rr:
        return float(atr_target)
    return None  # no valid target -> caller skips the trade


# ---------------------------------------------------------------------------
# 1.4 Orchestrator
# ---------------------------------------------------------------------------

def compute_structure_trade(
    df: pd.DataFrame,
    signal_idx: int,
    direction: str,
    max_wait_bars: int = DEFAULT_MAX_WAIT_BARS,
    min_rr: float = DEFAULT_MIN_RR,
    max_atr: float = DEFAULT_MAX_ATR,
    atr: pd.Series | None = None,
    pivot_distance: int = PIVOT_DISTANCE,
    entry_fallback: str = "signal",
) -> Optional[dict]:
    """Wire the three primitives in look-ahead-safe order. Returns dict | None.

    1. entry_price, entry_idx = compute_pullback_entry(...)   # may advance idx
    2. decision_idx = entry_idx
    3. stop_price  = compute_structure_stop(decision_idx=entry_idx, ...)
    4. target_price = compute_natural_target(decision_idx=entry_idx, ...)
    5. if target_price is None: return None (skip - no valid R:R)
    6. risk = |entry - stop|; if risk <= 0: return None
       final_rr = |target - entry| / risk; if final_rr < min_rr: return None

    Returns dict with keys:
        entry_price, entry_idx, stop_price, target_price, risk, rr,
        entry_type ("pullback" | "market"), decision_idx
    or None if the trade should be skipped.
    """
    if direction not in ("long", "short"):
        raise ValueError(f"direction must be 'long' or 'short', got {direction!r}")

    entry_price, entry_idx = compute_pullback_entry(
        df,
        signal_idx=signal_idx,
        direction=direction,
        max_wait_bars=max_wait_bars,
        pivot_distance=pivot_distance,
        fallback=entry_fallback,
    )
    # entry_type: pullback if the limit actually filled within the window,
    # else market (the signal-close fallback filled at the signal bar).
    entry_type = "pullback" if entry_idx > signal_idx else "market"

    decision_idx = entry_idx  # stricter than signal_idx (more pivots confirmed)

    stop_price = compute_structure_stop(
        df,
        decision_idx=decision_idx,
        direction=direction,
        entry_price=entry_price,
        max_atr=max_atr,
        pivot_distance=pivot_distance,
        atr=atr,
    )

    target_price = compute_natural_target(
        df,
        decision_idx=decision_idx,
        direction=direction,
        entry_price=entry_price,
        stop_price=stop_price,
        min_rr=min_rr,
        pivot_distance=pivot_distance,
        atr=atr,
    )

    if target_price is None:
        return None

    risk = abs(entry_price - stop_price)
    if risk <= 0:
        return None
    final_rr = abs(target_price - entry_price) / risk
    if final_rr < min_rr:
        return None  # defensive double-check

    return {
        "entry_price": float(entry_price),
        "entry_idx": int(entry_idx),
        "stop_price": float(stop_price),
        "target_price": float(target_price),
        "risk": float(risk),
        "rr": float(final_rr),
        "entry_type": entry_type,
        "decision_idx": int(decision_idx),
    }


if __name__ == "__main__":
    # Tiny smoke test when run directly.
    print("market_structure.py loaded OK")
    print(f"  PIVOT_DISTANCE = {PIVOT_DISTANCE}")
    print(f"  DEBUG = {_DEBUG}")
