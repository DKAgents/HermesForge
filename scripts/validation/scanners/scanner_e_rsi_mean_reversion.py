"""
scanner_e_rsi_mean_reversion.py
================================
HermesForge Phase 1A — Strategy E: RSI Mean-Reversion at Extremes

Entry logic (bidirectional, mirrors like scanner_b):

LONG signal:
  RSI(14) crosses UP through 30 (prev bar RSI < 30, current bar RSI >= 30) —
  confirms the oversold bounce is starting, not catching a falling knife
  mid-plunge.

SHORT signal:
  RSI(14) crosses DOWN through 70 (prev bar RSI > 70, current bar RSI <= 70).

Entry price = close of the signal bar.

Stop price:
  Long  = low of signal bar  - 0.25 * ATR(14)
  Short = high of signal bar + 0.25 * ATR(14)

Target price:
  risk   = abs(entry - stop)
  reward = max(2 * risk, abs(sma20 - entry))
  target = entry + reward * sign        (sign = +1 long, -1 short)

Filters:
  - Skip if R:R < 2.0 (reward / risk)
  - Skip if stop == entry (zero range)

Exit simulation (forward scan up to 8 bars):
  Long  : target = close >= target_price ; stop = close <= stop_price
  Short : target = close <= target_price ; stop = close >= stop_price
  'time' if neither hit within 8 bars.

Output fields per signal:
  ticker, date, entry_price, stop_price, target_price, direction,
  exit_price, exit_reason, bars_held, r_multiple, subperiod, strategy_id

Dependencies: pandas, numpy only.
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID  = "STR-E-rsi-mean-reversion"
RSI_PERIOD   = 14
ATR_PERIOD   = 14
SMA_PERIOD   = 20
ATR_STOP_MULT = 0.25
MIN_RR       = 2.0
MAX_HOLD     = 8
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
LOOKBACK     = 20   # SMA20 / ATR14 warmup, use 20 for safety margin


def _subperiod(date: "pd.Timestamp | pd.NaTType") -> str:  # type: ignore[name-defined]
    """Assign a calendar sub-period label (quarter) to a date."""
    ts = pd.Timestamp(str(date))
    return f"{ts.year}-Q{ts.quarter}"


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder-smoothed RSI (EWM, alpha = 1/period)."""
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs       = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                  period: int = 14) -> pd.Series:
    """Average True Range (Wilder smoothing via EWM)."""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _compute_sma(close: pd.Series, period: int = 20) -> pd.Series:
    return close.rolling(window=period).mean()


def _simulate_exit(
    closes: np.ndarray,
    entry_idx: int,
    entry_price: float,
    stop_price: float,
    target_price: float,
    direction: str,          # 'long' or 'short'
    max_bars: int = MAX_HOLD,
) -> tuple:
    """
    Scan forward from bar after entry_idx for up to max_bars bars.
    For 'long'  : target = close >= target_price ; stop = close <= stop_price
    For 'short' : target = close <= target_price ; stop = close >= stop_price
    Returns (exit_price, exit_reason, bars_held).
    """
    n = len(closes)
    for offset in range(1, max_bars + 1):
        idx = entry_idx + offset
        if idx >= n:
            last = min(entry_idx + offset - 1, n - 1)
            return closes[last], "time", offset
        c = closes[idx]
        if direction == "long":
            if c >= target_price:
                return c, "target", offset
            if c <= stop_price:
                return c, "stop", offset
        else:  # short
            if c <= target_price:
                return c, "target", offset
            if c >= stop_price:
                return c, "stop", offset

    exit_idx = min(entry_idx + max_bars, n - 1)
    return closes[exit_idx], "time", max_bars


def scan(df: pd.DataFrame, ticker: str) -> list[dict]:
    """
    Scan df for Strategy E — RSI Mean-Reversion at Extremes (both directions).

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV data with DatetimeIndex and columns:
        open, high, low, close, volume
    ticker : str
        Ticker symbol (for output tagging)

    Returns
    -------
    list of dict, one per signal
    """
    df = df.copy()
    df.columns = df.columns.str.lower()
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(df.columns):
        raise ValueError(f"DataFrame missing columns: {required - set(df.columns)}")
    df.sort_index(inplace=True)

    close = df["close"]
    high  = df["high"]
    low   = df["low"]

    # --- Compute indicators ---
    rsi   = _compute_rsi(close, period=RSI_PERIOD)
    atr   = _compute_atr(high, low, close, period=ATR_PERIOD)
    sma20 = _compute_sma(close, period=SMA_PERIOD)

    close_arr = close.values.astype(float)
    high_arr  = high.values.astype(float)
    low_arr   = low.values.astype(float)
    rsi_arr   = rsi.values.astype(float)
    atr_arr   = atr.values.astype(float)
    sma_arr   = sma20.values.astype(float)
    dates     = df.index

    signals: list[dict] = []

    min_start = max(RSI_PERIOD, ATR_PERIOD, SMA_PERIOD, LOOKBACK) + 1

    for i in range(min_start, len(df)):

        if (np.isnan(rsi_arr[i]) or np.isnan(rsi_arr[i - 1]) or
                np.isnan(atr_arr[i]) or np.isnan(sma_arr[i])):
            continue

        entry_price = close_arr[i]

        # =====================================================================
        # LONG SIGNAL: RSI crosses UP through 30
        # =====================================================================
        if rsi_arr[i - 1] < RSI_OVERSOLD and rsi_arr[i] >= RSI_OVERSOLD:
            stop_price = low_arr[i] - ATR_STOP_MULT * atr_arr[i]
            risk = entry_price - stop_price
            if risk <= 0:
                pass
            else:
                reward = max(2 * risk, abs(sma_arr[i] - entry_price))
                target_price = entry_price + reward
                rr = reward / risk
                if rr >= MIN_RR:
                    ep, er, bh = _simulate_exit(
                        close_arr, i, entry_price, stop_price, target_price, "long"
                    )
                    r_mult = (ep - entry_price) / risk
                    ts = pd.Timestamp(str(dates[i]))
                    signals.append({
                        "ticker":       ticker,
                        "date":         ts.date(),
                        "entry_price":  round(entry_price, 4),
                        "stop_price":   round(stop_price, 4),
                        "target_price": round(target_price, 4),
                        "direction":    "long",
                        "exit_price":   round(ep, 4),
                        "exit_reason":  er,
                        "bars_held":    bh,
                        "r_multiple":   round(r_mult, 4),
                        "subperiod":    _subperiod(ts),
                        "strategy_id":  STRATEGY_ID,
                    })

        # =====================================================================
        # SHORT SIGNAL: RSI crosses DOWN through 70
        # =====================================================================
        if rsi_arr[i - 1] > RSI_OVERBOUGHT and rsi_arr[i] <= RSI_OVERBOUGHT:
            stop_price = high_arr[i] + ATR_STOP_MULT * atr_arr[i]
            risk = stop_price - entry_price
            if risk <= 0:
                continue
            reward = max(2 * risk, abs(sma_arr[i] - entry_price))
            target_price = entry_price - reward
            rr = reward / risk
            if rr < MIN_RR:
                continue
            ep, er, bh = _simulate_exit(
                close_arr, i, entry_price, stop_price, target_price, "short"
            )
            r_mult = (entry_price - ep) / risk
            ts = pd.Timestamp(str(dates[i]))
            signals.append({
                "ticker":       ticker,
                "date":         ts.date(),
                "entry_price":  round(entry_price, 4),
                "stop_price":   round(stop_price, 4),
                "target_price": round(target_price, 4),
                "direction":    "short",
                "exit_price":   round(ep, 4),
                "exit_reason":  er,
                "bars_held":    bh,
                "r_multiple":   round(r_mult, 4),
                "subperiod":    _subperiod(ts),
                "strategy_id":  STRATEGY_ID,
            })

    return signals


# --------------------------------------------------------------------------- #
# __main__ : quick smoke test against cached SPY data                         #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import sys

    cache_path = Path.home() / ".hermes" / "market_data" / "SPY.parquet"
    if not cache_path.exists():
        print(f"[ERROR] Cache file not found: {cache_path}", file=sys.stderr)
        sys.exit(1)

    spy_df = pd.read_parquet(cache_path)
    print(f"Loaded SPY: {len(spy_df)} bars  ({spy_df.index[0]} -> {spy_df.index[-1]})")

    results = scan(spy_df, "SPY")
    print(f"\nStrategy E signals found: {len(results)}")

    if results:
        print("\nFirst 3 signals:")
        for sig in results[:3]:
            for k, v in sig.items():
                print(f"  {k:25s}: {v}")
            print()
