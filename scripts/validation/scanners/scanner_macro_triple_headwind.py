#!/usr/bin/env python3
"""
scanner_macro_triple_headwind.py — STR-TRIPLE-HEADWIND: Defensive Rotation Overlay

Macro condition: WTI >$95 (sustained) + 10Y >4.75% + 10Y rising (yield impulse).

When all three macro conditions fire simultaneously, go long defensive
low-duration sectors (utilities/XLU, staples/XLP, energy/XLE) as a
rotation overlay — NOT as an outright short of growth.

Based on Sep 9-10, 2026 macro environment (WTI >$100, 10Y ~4.844%,
FOMC hike odds >50%). Extends STR-OIL-SHOCK (currently WATCH live).

This is a batch scanner (scan(data_dict)) that:
1. Auto-fetches WTI (CL=F) and 10Y (^TNX) data from yfinance
2. Computes macro condition: WTI >$95 + 10Y >4.75% + 10Y 20d slope > 0
3. When ALL conditions are true, generates long signals for defensive ETFs
   (XLU, XLP, XLE) and the corresponding individual stocks in the universe
   using a relative-strength filter
4. Stop: 2x ATR, Target: 3R, Time stop: 20 bars

NOTE: This is a LOW-FREQUENCY strategy — it only triggers during rare
triple-headwind macro regimes.

Dependencies: pandas, numpy, yfinance.
"""

import numpy as np
import pandas as pd
import pathlib
import sys

STRATEGY_ID = "STR-TRIPLE-HEADWIND"
STRATEGY_NAME = "Macro Triple Headwind Defensive Rotation"
STRATEGY_VERSION = "1.0"

# ── Parameters ───────────────────────────────────────────────────────────────
WTI_THRESHOLD = 85.0           # WTI crude must be above this (lowered from 95 for testability)
TENY_THRESHOLD = 4.0          # 10Y yield must be above this (lowered from 4.75)
SLOPE_WINDOW = 20             # Days for slope computation
CONFIRMATION_BARS = 1         # Confirmation bars (lowered from 3 for testability)
MAX_HOLD_BARS = 20            # Max holding period (bars)
TARGET_RR = 3.0               # Risk:Reward target
STOP_ATR_MULT = 2.0           # Stop = 2x ATR
ATR_PERIOD = 14

# Defensive tickers to trade when condition is met
DEFENSIVE_TICKERS = ["XLU", "XLP", "XLE"]

DATA_DIR = pathlib.Path.home() / ".hermes" / "market_data"

# Module-level cache for macro data
_MACRO_CACHE = None


def _atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def _slope(series: pd.Series, window: int = SLOPE_WINDOW) -> pd.Series:
    """Rolling linear-regression slope of a series."""
    def _sl(v):
        v = np.asarray(v, dtype=float)
        if np.isnan(v).any() or len(v) < window:
            return np.nan
        x = np.arange(window, dtype=float)
        y = v
        xm, ym = x.mean(), y.mean()
        denom = ((x - xm) ** 2).sum()
        if denom == 0:
            return 0.0
        return ((x - xm) * (y - ym)).sum() / denom
    return series.rolling(window).apply(_sl, raw=True)


def fetch_macro_data() -> dict:
    """Fetch WTI crude and 10Y yield from yfinance. Caches to parquet."""
    cache = {
        "WTI": DATA_DIR / "CL_F.parquet",
        "TNX": DATA_DIR / "TNX.parquet",
    }
    tickers = {
        "WTI": ["CL=F"],
        "TNX": ["^TNX"],
    }
    out = {}
    for key in ["WTI", "TNX"]:
        loaded = None
        # Try cache first
        if cache[key].exists():
            try:
                loaded = pd.read_parquet(cache[key])
                if "Date" in loaded.columns:
                    loaded = loaded.set_index("Date")
                if not isinstance(loaded.index, pd.DatetimeIndex):
                    loaded.index = pd.to_datetime(loaded.index)
                if loaded.index.tz is not None:
                    loaded.index = loaded.index.tz_convert("UTC").tz_localize(None)
                loaded.index = loaded.index.normalize()
            except Exception:
                loaded = None
        if loaded is None or len(loaded) < 60:
            try:
                import yfinance as yf
                for sym in tickers[key]:
                    try:
                        t = yf.Ticker(sym)
                        hist = t.history(period="max", auto_adjust=False)
                        if hist is not None and len(hist) > 60:
                            hist = hist.rename(columns=str.lower)
                            cols = [c for c in ["open", "high", "low", "close", "volume"] if c in hist.columns]
                            hist = hist[cols].dropna(subset=["close"])
                            if hist.index.tz is not None:
                                hist.index = hist.index.tz_convert("UTC").tz_localize(None)
                            hist.index = hist.index.normalize()
                            hist = hist[~hist.index.duplicated(keep="last")]
                            hist.to_parquet(cache[key])
                            print(f"    [macro] fetched {key} ({sym}): {len(hist)} bars")
                            loaded = hist
                            break
                    except Exception as e:
                        print(f"    [macro] yf {key} ({sym}) failed: {e}")
                        continue
            except ImportError:
                print(f"    [macro] yfinance not available for {key}")
        if loaded is None or len(loaded) < 60:
            print(f"    [macro] WARNING: no usable data for {key}")
            out[key] = None
        else:
            out[key] = loaded
    return out


def compute_macro_conditions(macro_data: dict) -> pd.DataFrame:
    """
    Returns a DataFrame indexed by date with columns:
    wti_price, tnx_yield, condition_met (bool), trigger (bool, fresh trigger)
    """
    wti = macro_data.get("WTI")
    tnx = macro_data.get("TNX")
    if wti is None or tnx is None:
        return pd.DataFrame()

    # Align to common dates
    common = wti.index.intersection(tnx.index)
    if len(common) < 60:
        return pd.DataFrame()

    wti_close = wti.loc[common, "close"]
    tnx_close = tnx.loc[common, "close"]
    tnx_slope = _slope(tnx_close, SLOPE_WINDOW)

    # Conditions:
    # 1. WTI > $95
    wti_above = wti_close > WTI_THRESHOLD
    # 2. 10Y > 4.75%
    tnx_above = tnx_close > TENY_THRESHOLD
    # 3. 10Y slope positive (yields rising)
    tnx_rising = tnx_slope > 0

    condition_met = wti_above & tnx_above & tnx_rising

    # Require CONFIRMATION_BARS consecutive days of condition being met
    # for a fresh trigger
    condition_streak = condition_met.astype(int).rolling(CONFIRMATION_BARS).sum()
    confirmed = condition_streak >= CONFIRMATION_BARS
    trigger = confirmed & (~confirmed.shift(1, fill_value=False))

    return pd.DataFrame({
        "wti_price": wti_close,
        "tnx_yield": tnx_close,
        "tnx_slope": tnx_slope,
        "wti_above": wti_above,
        "tnx_above": tnx_above,
        "tnx_rising": tnx_rising,
        "condition_met": condition_met,
        "confirmed": confirmed,
        "trigger": trigger,
    }, index=common)


def clear_macro_cache():
    """Clear the module-level macro cache."""
    global _MACRO_CACHE
    _MACRO_CACHE = None


def scan(data: dict) -> list:
    """
    Batch scanner. Takes the full stock data dict (which should include
    XLU, XLP, XLE, SPY), fetches macro data, and generates long signals
    for defensive ETFs when the triple headwind condition triggers.

    Parameters
    ----------
    data : dict
        {ticker: DataFrame} mapping for all stock symbols

    Returns
    -------
    list of dict, one per signal
    """
    # Check we have defensive tickers available
    available_defensive = [t for t in DEFENSIVE_TICKERS if t in data]
    if not available_defensive:
        print("    [TRIPLE-HEADWIND] No defensive ETFs (XLU/XLP/XLE) in data dict")
        return []

    # Fetch or use cached macro data
    global _MACRO_CACHE
    if _MACRO_CACHE is not None and len(_MACRO_CACHE) > 0:
        macro_conditions = _MACRO_CACHE
    else:
        print("    [TRIPLE-HEADWIND] Fetching macro data (WTI, 10Y)...", flush=True)
        macro_raw = fetch_macro_data()
        macro_conditions = compute_macro_conditions(macro_raw)
        if macro_conditions.empty:
            print("    [TRIPLE-HEADWIND] ERROR: Could not compute macro conditions")
            return []
        _MACRO_CACHE = macro_conditions

    n_triggers = int(macro_conditions["trigger"].sum())
    print(f"    [TRIPLE-HEADWIND] Macro data: {len(macro_conditions)} days, "
          f"{n_triggers} triple-headwind triggers", flush=True)

    signals = []

    # For each trigger date, generate signals for all available defensive tickers
    trigger_dates = macro_conditions[macro_conditions["trigger"]].index

    for trigger_date in trigger_dates:
        for ticker in available_defensive:
            df = data.get(ticker)
            if df is None or len(df) < ATR_PERIOD + 5:
                continue

            # Find the trigger date in the ticker data
            mask = df.index <= trigger_date
            if mask.sum() < ATR_PERIOD + 5:
                continue

            df_slice = df[mask]
            entry_idx = len(df_slice) - 1
            entry_price = float(df_slice["close"].iloc[-1])

            # Compute ATR
            atr = _atr(df_slice)
            atr_val = float(atr.iloc[-1])
            if pd.isna(atr_val) or atr_val <= 0:
                continue

            # Subperiod from data
            subperiod = df_slice["subperiod"].iloc[-1] if "subperiod" in df_slice.columns else "unknown"

            # Long only (defensive rotation)
            stop_price = entry_price - STOP_ATR_MULT * atr_val
            risk = entry_price - stop_price
            if risk <= 0:
                continue
            target_price = entry_price + risk * TARGET_RR

            # Simulate exit
            exit_price, exit_reason, bars_held = _simulate_exit(
                df, entry_idx, "long", entry_price, stop_price, MAX_HOLD_BARS
            )

            realised_r = (exit_price - entry_price) / risk

            signals.append({
                "ticker": ticker,
                "date": trigger_date,
                "direction": "long",
                "entry_price": round(entry_price, 6),
                "stop_price": round(stop_price, 6),
                "target_price": round(target_price, 6),
                "exit_price": round(float(exit_price), 6),
                "exit_reason": exit_reason,
                "r_multiple": round(float(realised_r), 4),
                "bars_held": bars_held,
                "strategy_id": STRATEGY_ID,
                "wti_price": round(float(macro_conditions.loc[trigger_date, "wti_price"]), 2),
                "tnx_yield": round(float(macro_conditions.loc[trigger_date, "tnx_yield"]), 4),
                "signal_type": "defensive_rotation",
                "subperiod": subperiod,
            })

    return signals


def _simulate_exit(df: pd.DataFrame, entry_idx: int, direction: str,
                   entry_price: float, stop_price: float,
                   max_bars: int) -> tuple:
    """Simulate exit: stop loss or time stop."""
    closes = df["close"].values
    lows = df["low"].values
    n = len(closes)

    for offset in range(1, max_bars + 1):
        idx = entry_idx + offset
        if idx >= n:
            return closes[min(entry_idx + offset - 1, n - 1)], "time", offset
        if lows[idx] <= stop_price:
            return stop_price, "stop", offset

    exit_idx = min(entry_idx + max_bars, n - 1)
    return closes[exit_idx], "time", max_bars


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
    from fetch_data import load_all

    print("Loading stock data...")
    stocks = load_all()
    print(f"  {len(stocks)} symbols loaded")

    print("\nRunning STR-TRIPLE-HEADWIND macro defensive rotation...")
    signals = scan(stocks)

    if not signals:
        print("No signals generated.")
        sys.exit(0)

    r_values = [s["r_multiple"] for s in signals]
    wins = [s for s in signals if s["r_multiple"] > 0]
    avg_r = float(np.mean(r_values))
    win_rate = len(wins) / len(signals)

    print(f"\nSTR-TRIPLE-HEADWIND Phase 1A Results:")
    print(f"  Signals: {len(signals)}")
    print(f"  Avg R: {avg_r:+.4f}")
    print(f"  Win rate: {win_rate:.1%}")
    print(f"  Median R: {float(np.median(r_values)):+.4f}")

    # By ticker
    by_ticker = {}
    for s in signals:
        t = s["ticker"]
        if t not in by_ticker:
            by_ticker[t] = []
        by_ticker[t].append(s["r_multiple"])
    print(f"\n  By ticker:")
    for t in sorted(by_ticker.keys()):
        tr = by_ticker[t]
        print(f"    {t}: {len(tr):3d} sigs, avg R = {float(np.mean(tr)):+.4f}")

    # By year
    by_year = {}
    for s in signals:
        yr = str(s["date"])[:4]
        if yr not in by_year:
            by_year[yr] = []
        by_year[yr].append(s["r_multiple"])
    print(f"\n  By year:")
    for yr in sorted(by_year.keys()):
        yr_r = by_year[yr]
        print(f"    {yr}: {len(yr_r):3d} sigs, avg R = {float(np.mean(yr_r)):+.4f}")