#!/usr/bin/env python3
"""
scanner_vixfg_divergence.py — STR-VIXFG-DIVERGENCE: VIX vs Fear & Greed Divergence
====================================================================================

Phase 1A scanner. Batch mode (scan(data_dict)).

Hypothesis: When VIX (<16, declining WoW) and CNN Fear & Greed (<35, declining)
diverge significantly (>10 point adjusted gap), the market resolves in the VIX
(complacent) direction ~60% of the time: volatility stays low and equities drift
higher as the fear gauge recovers from extreme fear while options market stays calm.

Signal rules:
  1. VIX < 16 (complacent zone)
  2. CNN F&G < 35 (Fear territory)
  3. Normalized divergence gap > 10 points
  4. Both declining WoW (weekly negative change)
  5. Entry: Long SPY with stop at 20-day SMA
  6. Target: F&G > 50 or 3R
  7. Time stop: 20 trading days

Dependencies: pandas, numpy, yfinance.
"""

import numpy as np
import pandas as pd
import pathlib
import sys

STRATEGY_ID = "STR-VIXFG-DIVERGENCE"
STRATEGY_NAME = "VIX/F&G Intra-Equity Sentiment Divergence"

# ── Parameters ────────────────────────────────────────────────────────────────
VIX_THRESHOLD = 16.0           # VIX must be below this (complacent)
FG_THRESHOLD = 35.0            # F&G must be below this (fear)
DIVERGENCE_GAP_MIN = 10.0      # Minimum normalized gap between VIX and F&G
WO_WINDOW = 5                  # Week-over-week window (trading days)
MAX_HOLD_BARS = 20             # Time stop (20 trading days)
STOP_ATR_MULT = 2.0            # Stop = 2x ATR (but also check 20-day SMA)
MIN_RR = 1.5                   # Minimum R:R to proceed
SMA_STOP_PERIOD = 20           # 20-day SMA as trailing stop level
TARGET_RR = 3.0                # Target R:R
TARGET_FG_RECOVERY = 50.0      # Exit if F&G recovers above this

BENCHMARK = "SPY"
DATA_DIR = pathlib.Path.home() / ".hermes" / "market_data"
FG_CACHE_PATH = DATA_DIR / "fear_greed.parquet"


def _load_fg() -> pd.DataFrame | None:
    """Load Fear & Greed data from cache."""
    try:
        if FG_CACHE_PATH.exists():
            df = pd.read_parquet(FG_CACHE_PATH)
            if not df.empty and "value" in df.columns and "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                df = df.sort_values("date").set_index("date")
                return df
    except Exception as e:
        print(f"  [VIXFG] Failed to load F&G: {e}")
    return None


def _load_vix_historical() -> pd.DataFrame | None:
    """Fetch ^VIX historical data from yfinance."""
    try:
        import yfinance as yf
        vix = yf.download("^VIX", start="2018-01-01", progress=False)
        if vix is not None and not vix.empty:
            df = vix[["Close"]].copy().rename(columns={"Close": "close"})
            df.index = pd.to_datetime(df.index)
            df["close"] = df["close"].astype(float)
            return df
    except Exception as e:
        print(f"  [VIXFG] Failed to fetch VIX: {e}")
    return None


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def scan(data_dict: dict) -> list[dict]:
    """
    Batch-mode scanner for VIX/F&G Intra-Equity Divergence.

    Parameters
    ----------
    data_dict : dict
        {ticker: pd.DataFrame} with OHLCV daily data. Must include SPY.

    Returns
    -------
    list of dict, one per signal detected
    """
    # ── Validate required tickers ────────────────────────────────────────────
    if BENCHMARK not in data_dict:
        print(f"  [VIXFG] Missing {BENCHMARK} in data dict")
        return []

    # ── Load SPY data ────────────────────────────────────────────────────────
    df_spy = data_dict[BENCHMARK].copy()
    df_spy.sort_index(inplace=True)
    if "subperiod" not in df_spy.columns:
        df_spy["subperiod"] = df_spy.index.to_period("Q").astype(str)

    spy_close = df_spy["close"]
    spy_dates = df_spy.index
    subperiod_arr = df_spy["subperiod"].values

    # ── Load VIX data ────────────────────────────────────────────────────────
    df_vix = _load_vix_historical()
    if df_vix is None:
        print("  [VIXFG] Cannot proceed without VIX data")
        return []

    # ── Load F&G data ─────────────────────────────────────────────────────────
    df_fg = _load_fg()
    if df_fg is None:
        print("  [VIXFG] Cannot proceed without F&G data")
        return []

    # ── Align all data on SPY dates (daily intersection) ──────────────────────
    # VIX and SPY share trading days; F&G has a date per day
    # We'll merge VIX and F&G onto the SPY index

    # Reindex VIX to SPY dates (forward-fill for any gaps)
    vix_on_spy = df_vix["close"].reindex(spy_dates, method="ffill")

    # Reindex F&G to SPY dates (the F&G index covers every day)
    fg_on_spy = df_fg["value"].reindex(spy_dates, method="ffill")

    # Build aligned arrays
    vix_arr = vix_on_spy.values
    fg_arr = fg_on_spy.values
    spy_arr = spy_close.values

    # ── Compute indicators ────────────────────────────────────────────────────
    # VIX WoW change (5-day diff)
    vix_wow = pd.Series(vix_arr, index=spy_dates).diff(WO_WINDOW)
    fg_wow = pd.Series(fg_arr, index=spy_dates).diff(WO_WINDOW)

    # Normalized divergence: VIX_adjusted = (VIX / max(VIX)) * 100
    # Then gap = |VIX_adjusted - F&G|
    vix_max = max(np.nanmax(vix_arr), 1.0)
    vix_adj = (vix_arr / vix_max) * 100
    divergence_gap = np.abs(vix_adj - fg_arr)

    # ATR for stop sizing
    atr_vals = _atr(df_spy).values

    # 20-day SMA
    sma20 = spy_close.rolling(20, min_periods=20).mean().values

    signals = []

    min_start = WO_WINDOW + 25  # Enough lookback for WoW + SMA20

    for i in range(min_start, len(spy_dates)):
        # ── Check condition 1: VIX < threshold (complacent) ──────────────────
        if np.isnan(vix_arr[i]) or vix_arr[i] >= VIX_THRESHOLD:
            continue

        # ── Check condition 2: F&G < threshold (fear) ────────────────────────
        if np.isnan(fg_arr[i]) or fg_arr[i] >= FG_THRESHOLD:
            continue

        # ── Check condition 3: Divergence gap > minimum ──────────────────────
        if np.isnan(divergence_gap[i]) or divergence_gap[i] < DIVERGENCE_GAP_MIN:
            continue

        # ── Check condition 4: Both declining WoW ────────────────────────────
        if np.isnan(vix_wow.iloc[i]) or vix_wow.iloc[i] >= 0:
            continue  # VIX not declining
        if np.isnan(fg_wow.iloc[i]) or fg_wow.iloc[i] >= 0:
            continue  # F&G not declining

        # ── We have a signal! ─────────────────────────────────────────────────
        entry_price = float(spy_arr[i])
        current_vix = float(vix_arr[i])
        current_fg = float(fg_arr[i])

        # Stop: max of 2x ATR and 20-day SMA
        atr_stop = entry_price - (atr_vals[i] * STOP_ATR_MULT) if not np.isnan(atr_vals[i]) else 0
        sma_stop = sma20[i] if not np.isnan(sma20[i]) else 0
        stop_price = max(atr_stop, sma_stop)
        if stop_price <= 0:
            stop_price = entry_price * 0.97  # 3% stop as fallback

        # Risk
        risk = entry_price - stop_price
        if risk <= 0 or risk / entry_price < 0.005:
            continue

        # Target: 3R
        target_price = entry_price + risk * TARGET_RR

        # Min R:R filter
        reward = target_price - entry_price
        if reward / risk < MIN_RR:
            continue

        # ── Exit simulation ──────────────────────────────────────────────────
        exit_price = entry_price
        exit_reason = "time"
        bars_held = MAX_HOLD_BARS

        for offset in range(1, min(MAX_HOLD_BARS + 1, len(spy_dates) - i)):
            idx_exit = i + offset
            c = float(spy_arr[idx_exit])

            # Check stop
            if c <= stop_price:
                exit_price = c
                exit_reason = "stop"
                bars_held = offset
                break

            # Check target
            if c >= target_price:
                exit_price = c
                exit_reason = "target"
                bars_held = offset
                break

            # Check F&G recovery (early exit if fear resolves)
            if not np.isnan(fg_arr[idx_exit]) and fg_arr[idx_exit] >= TARGET_FG_RECOVERY:
                exit_price = c
                exit_reason = "fg_recovery"
                bars_held = offset
                break

        # R-multiple
        realised_r = (exit_price - entry_price) / risk

        # ── Build output record ──────────────────────────────────────────────
        signal = {
            "ticker": BENCHMARK,
            "date": spy_dates[i],
            "direction": "long",
            "entry_price": round(entry_price, 4),
            "stop_price": round(stop_price, 4),
            "target_price": round(target_price, 4),
            "exit_price": round(exit_price, 4),
            "exit_reason": exit_reason,
            "r_multiple": round(realised_r, 4),
            "bars_held": bars_held,
            "subperiod": subperiod_arr[i],
            "strategy_id": STRATEGY_ID,
            "vix": round(current_vix, 2),
            "fear_greed": int(current_fg),
            "divergence_gap": round(divergence_gap[i], 2),
            "vix_wow_change": round(float(vix_wow.iloc[i]), 2),
            "fg_wow_change": round(float(fg_wow.iloc[i]), 2),
        }
        signals.append(signal)

    return signals


if __name__ == "__main__":
    # Smoke test
    from fetch_data import load_all
    data = load_all()
    if not data:
        print("No data loaded.")
        sys.exit(1)
    results = scan(data)
    print(f"VIX/F&G Divergence signals found: {len(results)}")
    if results:
        for sig in results[:5]:
            print(f"  {sig['date']} | VIX={sig['vix']:.1f} F&G={sig['fear_greed']} "
                  f"gap={sig['divergence_gap']:.1f} | R={sig['r_multiple']:.3f} | {sig['exit_reason']}")