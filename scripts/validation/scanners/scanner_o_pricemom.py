#!/usr/bin/env python3
"""
scanner_o_pricemom.py — STR-O: Price Momentum Factor Strategy (Crypto-Optimized)

Built from factor decomposition evidence: PRICEMOM factor (price relative to
SMA200) showed +40% annualized return, p=0.04 in crypto. This strategy
expresses that factor as a per-ticker signal.

Signal Rules:
  1. PRICEMOM = close / SMA(N) - 1 (distance from moving average)
  2. Long when PRICEMOM > entry_threshold AND PRICEMOM is accelerating
     (current PRICEMOM > PRICEMOM N bars ago — momentum of momentum)
  3. Short when PRICEMOM < -entry_threshold AND PRICEMOM is decelerating
  4. Stop: ATR-based trailing (alpha * ATR)
  5. Exit: trailing stop hit or time stop

Distinct from STR-I (AdaptiveTrend):
  - STR-I uses rate-of-change momentum (price_t / price_{t-L} - 1)
  - STR-O uses distance-from-mean momentum (price / SMA - 1)
  - STR-O adds acceleration filter (momentum of momentum)
  - STR-O is designed for crypto where PRICEMOM factor is significant

Dependencies: pandas, numpy only.
"""

import numpy as np
import pandas as pd

STRATEGY_ID = "O_PRICEMOM"

# ── Parameters ───────────────────────────────────────────────────────────────
SMA_PERIOD = 200           # Moving average period for PRICEMOM
ENTRY_THRESHOLD = 0.15     # Minimum |PRICEMOM| for entry (15% above/below SMA)
ACCEL_LOOKBACK = 20        # Bars to measure PRICEMOM acceleration
ATR_PERIOD = 14             # ATR lookback
ATR_MULTIPLIER = 2.5        # Trailing stop multiplier
MIN_RR = 1.5                # Minimum R:R for signal reporting
MAX_BARS_HELD = 60          # Time stop (bars)
LONG_ONLY = False           # Crypto allows both directions


def _compute_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    """Average True Range (Wilder's smoothing)."""
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _simulate_trailing_exit(
    df: pd.DataFrame,
    entry_idx: int,
    direction: str,
    entry_price: float,
    initial_stop: float,
    atr_series: pd.Series,
) -> tuple:
    """
    Simulate ATR trailing stop from entry_idx forward.
    Returns (exit_price, exit_reason, bars_held, final_stop).
    """
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    atr_vals = atr_series.values
    alpha = ATR_MULTIPLIER

    if direction == "long":
        trailing_stop = initial_stop
        for j in range(entry_idx + 1, min(entry_idx + MAX_BARS_HELD + 1, len(closes))):
            new_stop = closes[j] - alpha * atr_vals[j]
            trailing_stop = max(trailing_stop, new_stop)
            if lows[j] <= trailing_stop:
                return trailing_stop, "stop", j - entry_idx, trailing_stop
        exit_idx = min(entry_idx + MAX_BARS_HELD, len(closes) - 1)
        return closes[exit_idx], "time", MAX_BARS_HELD, trailing_stop
    else:
        trailing_stop = initial_stop
        for j in range(entry_idx + 1, min(entry_idx + MAX_BARS_HELD + 1, len(closes))):
            new_stop = closes[j] + alpha * atr_vals[j]
            trailing_stop = min(trailing_stop, new_stop)
            if highs[j] >= trailing_stop:
                return trailing_stop, "stop", j - entry_idx, trailing_stop
        exit_idx = min(entry_idx + MAX_BARS_HELD, len(closes) - 1)
        return closes[exit_idx], "time", MAX_BARS_HELD, trailing_stop


def scan(df: pd.DataFrame, ticker: str = "", long_only: bool = LONG_ONLY) -> list:
    """
    Scan df for STR-O Price Momentum signals.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV data with DatetimeIndex
    ticker : str
        Ticker symbol
    long_only : bool
        If True, only generate long signals (for stocks)

    Returns
    -------
    list of dict, one per signal
    """
    df = df.copy()
    df.sort_index(inplace=True)

    if len(df) < SMA_PERIOD + ACCEL_LOOKBACK + 10:
        return []

    close = df["close"]
    high = df["high"]
    low = df["low"]

    # Compute PRICEMOM: distance from SMA
    sma = close.rolling(window=SMA_PERIOD).mean()
    pricemom = close / sma - 1

    # Compute PRICEMOM acceleration: is momentum increasing?
    pricemom_accel = pricemom - pricemom.shift(ACCEL_LOOKBACK)

    # ATR for stop placement
    atr = _compute_atr(df)

    # Convert to arrays
    close_arr = close.values.astype(float)
    pm_arr = pricemom.values.astype(float)
    pm_accel_arr = pricemom_accel.values.astype(float)
    atr_arr = atr.values.astype(float)
    dates = df.index

    signals = []
    min_start = SMA_PERIOD + ACCEL_LOOKBACK + 5

    # Track last signal to avoid clustering
    last_signal_bar = -999

    for i in range(min_start, len(df) - 1):
        # Skip if indicators not ready
        if np.isnan(pm_arr[i]) or np.isnan(pm_accel_arr[i]) or np.isnan(atr_arr[i]):
            continue

        # Avoid clustered signals (min 10 bars between signals)
        if i - last_signal_bar < 10:
            continue

        direction = None

        # ── Long signal: PRICEMOM > threshold AND accelerating ──────────────
        if pm_arr[i] > ENTRY_THRESHOLD and pm_accel_arr[i] > 0:
            direction = "long"

        # ── Short signal: PRICEMOM < -threshold AND decelerating ────────────
        if not long_only and pm_arr[i] < -ENTRY_THRESHOLD and pm_accel_arr[i] < 0:
            direction = "short"

        if direction is None:
            continue

        entry_price = close_arr[i]
        atr_val = atr_arr[i]

        if direction == "long":
            stop_price = entry_price - ATR_MULTIPLIER * atr_val
            # Target: 2x risk minimum
            risk = entry_price - stop_price
            target_price = entry_price + 2 * risk
        else:
            stop_price = entry_price + ATR_MULTIPLIER * atr_val
            risk = stop_price - entry_price
            target_price = entry_price - 2 * risk

        if risk <= 0:
            continue

        rr = abs(target_price - entry_price) / risk
        if rr < MIN_RR:
            continue

        # Simulate exit
        exit_price, exit_reason, bars_held, _ = _simulate_trailing_exit(
            df, i, direction, entry_price, stop_price, atr
        )

        # Compute R-multiple
        if direction == "long":
            realised_r = (exit_price - entry_price) / risk
        else:
            realised_r = (entry_price - exit_price) / risk

        signals.append({
            "ticker": ticker,
            "date": dates[i],
            "direction": direction,
            "entry_price": round(entry_price, 6),
            "stop_price": round(stop_price, 6),
            "target_price": round(target_price, 6),
            "exit_price": round(exit_price, 6),
            "exit_reason": exit_reason,
            "r_multiple": round(realised_r, 4),
            "bars_held": bars_held,
            "pricemom": round(float(pm_arr[i]), 4),
            "pricemom_accel": round(float(pm_accel_arr[i]), 4),
            "strategy_id": STRATEGY_ID,
        })

        last_signal_bar = i

    return signals


if __name__ == "__main__":
    import pathlib

    btc_path = pathlib.Path.home() / ".hermes" / "market_data" / "crypto" / "BTC.parquet"
    if btc_path.exists():
        df = pd.read_parquet(btc_path)
        results = scan(df, "BTC")
        print(f"STR-O signals on BTC: {len(results)}")
        long_sigs = [s for s in results if s["direction"] == "long"]
        short_sigs = [s for s in results if s["direction"] == "short"]
        print(f"  Long: {len(long_sigs)}, Short: {len(short_sigs)}")
        if results:
            avg_r = np.mean([s["r_multiple"] for s in results])
            win_rate = np.mean([1 if s["r_multiple"] > 0 else 0 for s in results])
            print(f"  Avg R: {avg_r:.4f}, Win rate: {win_rate:.1%}")
            print(f"\n  Last 5 signals:")
            for s in results[-5:]:
                print(f"    {s['date']} | {s['direction']:5s} | entry={s['entry_price']:.2f} | "
                      f"R={s['r_multiple']:+.4f} | PM={s['pricemom']:+.4f}")
