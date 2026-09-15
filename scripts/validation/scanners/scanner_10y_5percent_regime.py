#!/usr/bin/env python3
"""
scanner_10y_5percent_regime.py — STR-5PCT-REGIME: 10Y > 5% Regime Overlay

Edge candidate: CAND-20260915-10y-5percent-regime
Source hypothesis: When US 10Y yield breaches 5% (first time since 2007),
institutional behavior changes structurally — pension rebalancing, mortgage
convexity hedging, negative ERP for equities. This is a regime overlay that
reduces equity exposure and rotates to defensive sectors.

Signal Rules (batch):
  1. Regime active: TNX (^TNX) 10Y yield close >= TENY_THRESHOLD (5.0%)
  2. On regime trigger: long defensive (XLU, XLP, XLE), short growth (QQQ)
  3. Exit: ATR-based stop or time stop at MAX_BARS_HELD

NOTE: Since Oct 2018 (start of stock universe), TNX has never closed above
5.0% (max 4.988% on 2023-10-19). This scanner will produce ZERO signals
with the current data window. It exists as a structural framework that
activates when/if TNX data is refreshed to include the Sep 14-15, 2026
5.0% breach. The edge is better implemented as a forward-looking regime
overlay in regime_strategy_selector.py than as a backtested scanner.

Dependencies: pandas, numpy.
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "STR-5PCT-REGIME"
STRATEGY_NAME = "10Y > 5% Regime Overlay"

# ── Parameters ───────────────────────────────────────────────────────────────
TENY_THRESHOLD = 5.0          # 10Y yield close must be >= this
CONFIRMATION_BARS = 1          # Days of consecutive trigger to confirm
MAX_HOLD_BARS = 20             # Max holding period (bars)
TARGET_RR = 2.0                # Risk:Reward target
STOP_ATR_MULT = 2.0            # Stop = 2x ATR
ATR_PERIOD = 14
MIN_HISTORY = 60              # Need >= this many data points

# Tickers for rotation
LONG_TICKERS = ["XLU", "XLP", "XLE"]       # Defensive: utilities, staples, energy
SHORT_TICKERS = ["QQQ", "SPY"]              # Growth/market: tech, broad market

DATA_DIR = Path.home() / ".hermes" / "market_data"

# Module-level cache
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


def _subperiod(date) -> str:
    if pd.isna(date):
        return "unknown"
    d = date.date() if hasattr(date, "date") else date
    if d < pd.Timestamp("2019-04-01").date():
        return "pre_warmup"
    if d <= pd.Timestamp("2021-12-31").date():
        return "period1_bull"
    if d <= pd.Timestamp("2023-12-31").date():
        return "period2_bear"
    return "period3_current"


def fetch_macro_data() -> dict:
    """Load TNX yield data from parquet cache."""
    out = {}
    tnx_path = DATA_DIR / "TNX.parquet"
    if tnx_path.exists():
        tnx = pd.read_parquet(tnx_path)
        tnx.columns = [c.lower() for c in tnx.columns]
        tnx = tnx.sort_index()
        tnx = tnx[~tnx.index.duplicated(keep="last")]
        out["TNX"] = tnx
    return out


def compute_regime(macro_data: dict) -> pd.Series:
    """
    Returns a boolean Series: regime_active (TNX close >= TENY_THRESHOLD).
    """
    tnx = macro_data.get("TNX")
    if tnx is None or not isinstance(tnx, pd.DataFrame) or len(tnx) < MIN_HISTORY:
        return pd.Series(dtype=bool)

    tnx_close = tnx["close"]
    above_threshold = tnx_close >= TENY_THRESHOLD

    # Require CONFIRMATION_BARS consecutive days
    if CONFIRMATION_BARS > 1:
        streak = above_threshold.astype(int).rolling(CONFIRMATION_BARS).sum()
        confirmed = streak >= CONFIRMATION_BARS
    else:
        confirmed = above_threshold

    return confirmed


def _simulate_exit(df: pd.DataFrame, entry_idx: int, direction: str,
                   entry_price: float, stop_price: float,
                   max_bars: int) -> tuple:
    """Simulate exit: stop loss or time stop. Returns (exit_price, reason, bars_held)."""
    closes = df["close"].values
    n = len(closes)

    for offset in range(1, max_bars + 1):
        idx = entry_idx + offset
        if idx >= n:
            return closes[min(entry_idx + offset - 1, n - 1)], "time", offset

        if direction == "long":
            if df["low"].iloc[idx] <= stop_price:
                return stop_price, "stop", offset
        else:  # short
            if df["high"].iloc[idx] >= stop_price:
                return stop_price, "stop", offset

    exit_idx = min(entry_idx + max_bars, n - 1)
    return closes[exit_idx], "time", max_bars


def scan(data: dict) -> list:
    """
    Batch scanner. Loads TNX, checks 10Y >= 5% regime, generates signals.
    """
    # Verify defensive/growth tickers exist in data
    available_long = [t for t in LONG_TICKERS if t in data]
    available_short = [t for t in SHORT_TICKERS if t in data]

    if not available_long and not available_short:
        print("    [5PCT-REGIME] No tradable tickers available in data dict")
        return []

    # Fetch macro data
    global _MACRO_CACHE
    if _MACRO_CACHE is not None:
        macro_data = _MACRO_CACHE
    else:
        macro_data = fetch_macro_data()
        tnx_df = macro_data.get("TNX")
        if tnx_df is None or not isinstance(tnx_df, pd.DataFrame):
            print("    [5PCT-REGIME] ERROR: No TNX data available")
            return []
        _MACRO_CACHE = macro_data

    regime = compute_regime(macro_data)
    n_active = int(regime.sum())
    print(f"    [5PCT-REGIME] TNX data: {len(regime)} days, "
          f"{n_active} regime-active days (TNX >= {TENY_THRESHOLD}%)", flush=True)

    if n_active == 0:
        print(f"    [5PCT-REGIME] WARNING: TNX never >= {TENY_THRESHOLD}% in available data. "
              "Data goes up to " + str(macro_data["TNX"].index[-1])[:10] + ". "
              "The Sep 2026 5% breach may not be in cache yet.", flush=True)
        return []

    # Find regime trigger dates (first active day after inactive period)
    trigger = regime & (~regime.shift(1, fill_value=False))
    trigger_dates = trigger[trigger].index

    print(f"    [5PCT-REGIME] {len(trigger_dates)} regime trigger events", flush=True)

    signals = []
    last_signal_date = None

    for trigger_date in trigger_dates:
        last_signal_date = trigger_date

        # --- Long signals (defensive rotation) ---
        for ticker in available_long:
            df = data.get(ticker)
            if df is None or len(df) < ATR_PERIOD + 5:
                continue

            mask = df.index <= trigger_date
            if mask.sum() < ATR_PERIOD + 5:
                continue

            df_slice = df[mask]
            entry_idx = len(df_slice) - 1
            entry_price = float(df_slice["close"].iloc[-1])

            atr = _atr(df_slice)
            atr_val = float(atr.iloc[-1])
            if pd.isna(atr_val) or atr_val <= 0:
                continue

            subperiod = df_slice["subperiod"].iloc[-1] if "subperiod" in df_slice.columns else _subperiod(trigger_date)

            stop_price = entry_price - STOP_ATR_MULT * atr_val
            risk = entry_price - stop_price
            if risk <= 0 or risk / entry_price < 0.002:
                continue
            target_price = entry_price + risk * TARGET_RR

            exit_price, exit_reason, bars_held = _simulate_exit(
                df, entry_idx, "long", entry_price, stop_price, MAX_HOLD_BARS
            )
            realised_r = (exit_price - entry_price) / risk

            signals.append({
                "ticker": ticker,
                "date": str(trigger_date.date()),
                "direction": "long",
                "entry_price": round(entry_price, 6),
                "stop_price": round(stop_price, 6),
                "target_price": round(target_price, 6),
                "exit_price": round(float(exit_price), 6),
                "exit_reason": exit_reason,
                "r_multiple": round(float(realised_r), 4),
                "bars_held": bars_held,
                "strategy_id": STRATEGY_ID,
                "subperiod": subperiod,
                "regime": "5pct_yield",
                "entry_type": "defensive_rotation",
            })

        # --- Short signals (growth/market — QQQ/SPY) ---
        for ticker in available_short:
            df = data.get(ticker)
            if df is None or len(df) < ATR_PERIOD + 5:
                continue

            mask = df.index <= trigger_date
            if mask.sum() < ATR_PERIOD + 5:
                continue

            df_slice = df[mask]
            entry_idx = len(df_slice) - 1
            entry_price = float(df_slice["close"].iloc[-1])

            atr = _atr(df_slice)
            atr_val = float(atr.iloc[-1])
            if pd.isna(atr_val) or atr_val <= 0:
                continue

            subperiod = df_slice["subperiod"].iloc[-1] if "subperiod" in df_slice.columns else _subperiod(trigger_date)

            stop_price = entry_price + STOP_ATR_MULT * atr_val
            risk = stop_price - entry_price
            if risk <= 0 or risk / entry_price < 0.002:
                continue
            target_price = entry_price - risk * TARGET_RR

            exit_price, exit_reason, bars_held = _simulate_exit(
                df, entry_idx, "short", entry_price, stop_price, MAX_HOLD_BARS
            )
            realised_r = (entry_price - exit_price) / risk

            signals.append({
                "ticker": ticker,
                "date": str(trigger_date.date()),
                "direction": "short",
                "entry_price": round(entry_price, 6),
                "stop_price": round(stop_price, 6),
                "target_price": round(target_price, 6),
                "exit_price": round(float(exit_price), 6),
                "exit_reason": exit_reason,
                "r_multiple": round(float(realised_r), 4),
                "bars_held": bars_held,
                "strategy_id": STRATEGY_ID,
                "subperiod": subperiod,
                "regime": "5pct_yield",
                "entry_type": "growth_short",
            })

    return signals


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from fetch_data import load_all

    print("Loading stock data...")
    stocks = load_all()
    print(f"  {len(stocks)} symbols loaded")

    print("\nRunning STR-5PCT-REGIME scanner...")
    signals = scan(stocks)

    if not signals:
        print("No signals generated — TNX never >= 5% in data window.")
        sys.exit(0)

    r_values = [s["r_multiple"] for s in signals]
    wins = [s for s in signals if s["r_multiple"] > 0]
    avg_r = float(np.mean(r_values)) if r_values else 0
    win_rate = len(wins) / len(signals) if signals else 0

    print(f"\nSTR-5PCT-REGIME Phase 1A Results:")
    print(f"  Signals: {len(signals)}")
    print(f"  Avg R: {avg_r:+.4f}")
    print(f"  Win rate: {win_rate:.1%}")