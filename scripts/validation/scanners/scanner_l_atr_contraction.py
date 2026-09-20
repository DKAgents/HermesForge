"""
scanner_l_atr_contraction.py
Strategy L — ATR Contraction Breakout

Entry logic (long-only):
  - ATR(14) is at its lowest level in trailing 120 bars
  - ADX(14) < 18 (non-trending confirmation)
  - Price closes above highest high of trailing 20 bars
  - Volume on breakout bar > 1.5x average 20-day volume
  - Price above 200-day SMA (trend filter)

Exit simulation (forward scan up to 20 bars):
  - Stop: breakout bar low
  - No fixed target — trailing stop only
  - Trailing stop: ATR(14) × 2.0 below highest close since entry
  - Time stop: 20 bars

Output fields per signal:
  ticker, date, entry_price, stop_price, target_price, direction,
  exit_price, exit_reason, bars_held, r_multiple, subperiod, strategy_id
"""

import pandas as pd
import numpy as np
from pathlib import Path

STRATEGY_ID = "STR-ATR-CONTRACTION-perasset"
ATR_PERIOD    = 14
ATR_LOW_LOOKBACK = 120
ADX_PERIOD    = 14
ADX_MAX       = 18
BREAKOUT_LOOKBACK = 20
VOLUME_MULT   = 1.5
SMA_PERIOD    = 200
TRAIL_ATR_MULT = 2.0
MAX_HOLD      = 20
MIN_BARS      = max(ATR_LOW_LOOKBACK, SMA_PERIOD) + 10


def _subperiod(date) -> str:
    """Assign a calendar sub-period label (quarter)."""
    ts = pd.Timestamp(str(date))
    return f"{ts.year}-Q{ts.quarter}"


def _compute_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    """Compute Average True Range."""
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(period).mean()


def _compute_adx(df: pd.DataFrame, period: int = ADX_PERIOD) -> pd.Series:
    """Compute ADX."""
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = _compute_atr(df, 1) * period  # raw TR * period for Wilder smoothing
    # Use smoothed TR
    atr_series = _compute_atr(df, period)
    plus_di = 100 * pd.Series(plus_dm, index=df.index).rolling(period).mean() / atr_series
    minus_di = 100 * pd.Series(minus_dm, index=df.index).rolling(period).mean() / atr_series
    # Handle zero division
    plus_di = plus_di.fillna(0).replace([np.inf, -np.inf], 0)
    minus_di = minus_di.fillna(0).replace([np.inf, -np.inf], 0)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    dx = dx.fillna(0).replace([np.inf, -np.inf], 0)
    return dx.rolling(period).mean()


def _simulate_exit(
    df: pd.DataFrame,
    entry_idx: int,
    entry_price: float,
    stop_price: float,
    atr_at_entry: float,
) -> dict:
    """
    Walk forward from the bar after entry for up to MAX_HOLD bars.
    Trailing stop: highest close since entry - (ATR * TRAIL_ATR_MULT).
    Initial stop is breakout bar low.
    """
    risk = entry_price - stop_price
    if risk <= 0:
        return dict(exit_price=entry_price, exit_reason="invalid", bars_held=0, r_multiple=0.0)

    n = len(df)
    current_stop = stop_price
    highest_close = entry_price

    for offset in range(1, MAX_HOLD + 1):
        bar_idx = entry_idx + offset
        if bar_idx >= n:
            last_close = df["close"].iloc[bar_idx - 1] if bar_idx > 0 else entry_price
            r_mult = (last_close - entry_price) / risk
            return dict(exit_price=round(last_close, 4), exit_reason="time",
                       bars_held=offset, r_multiple=round(r_mult, 3))

        close = df["close"].iloc[bar_idx]
        high = df["high"].iloc[bar_idx]
        low = df["low"].iloc[bar_idx]

        # Update highest close since entry
        if close > highest_close:
            highest_close = close

        # Update trailing stop: highest_close - ATR * multiplier
        # Use a constant ATR for simplicity (at_entry ATR as baseline)
        # In practice ATR should be recalculated, but for backtest simplicity:
        trail_stop = highest_close - (atr_at_entry * TRAIL_ATR_MULT)
        if trail_stop > current_stop:
            current_stop = trail_stop

        # Check if stopped out
        if low <= current_stop:
            exit_price = round(current_stop, 4)  # assume exit at stop level
            if exit_price < entry_price:
                r_mult = (exit_price - entry_price) / risk
            else:
                r_mult = (exit_price - entry_price) / risk
            return dict(exit_price=exit_price, exit_reason="stop",
                       bars_held=offset, r_multiple=round(r_mult, 3))

    # Time stop
    last_close = df["close"].iloc[entry_idx + MAX_HOLD] if entry_idx + MAX_HOLD < n else df["close"].iloc[-1]
    r_mult = (last_close - entry_price) / risk
    return dict(exit_price=round(last_close, 4), exit_reason="time",
               bars_held=MAX_HOLD, r_multiple=round(r_mult, 3))


def scan(df: pd.DataFrame, ticker: str) -> list[dict]:
    """Scan a price DataFrame for ATR Contraction Breakout signals."""
    df = df.copy()
    df.columns = df.columns.str.lower()
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(df.columns):
        raise ValueError(f"DataFrame missing columns: {required - set(df.columns)}")
    df = df.sort_index()

    if len(df) < MIN_BARS:
        return []

    # Compute indicators
    atr = _compute_atr(df, ATR_PERIOD)
    adx = _compute_adx(df, ADX_PERIOD)
    sma200 = df["close"].rolling(SMA_PERIOD).mean()
    avg_vol_20 = df["volume"].rolling(BREAKOUT_LOOKBACK).mean()
    highest_high_20 = df["high"].rolling(BREAKOUT_LOOKBACK).apply(
        lambda x: x.iloc[:-1].max() if len(x) >= 2 else np.nan, raw=False
    )
    atr_120_low = atr.rolling(ATR_LOW_LOOKBACK).min()

    signals: list[dict] = []

    for i in range(MIN_BARS, len(df)):
        date = df.index[i]
        close = df["close"].iloc[i]
        high = df["high"].iloc[i]
        low = df["low"].iloc[i]
        vol = df["volume"].iloc[i]

        # Filter checks
        if pd.isna(atr.iloc[i]) or pd.isna(adx.iloc[i]) or pd.isna(sma200.iloc[i]):
            continue
        if pd.isna(highest_high_20.iloc[i]) or pd.isna(atr_120_low.iloc[i]):
            continue
        if pd.isna(avg_vol_20.iloc[i]):
            continue

        # 1. ATR at 120-bar low
        if not np.isclose(atr.iloc[i], atr_120_low.iloc[i], rtol=1e-9):
            continue

        # 2. ADX < 18
        if adx.iloc[i] >= ADX_MAX:
            continue

        # 3. Breakout: close above prior 20-bar highest high
        prior_highest = highest_high_20.iloc[i]
        if pd.isna(prior_highest) or close <= prior_highest:
            continue

        # 4. Volume confirmation
        if vol < avg_vol_20.iloc[i] * VOLUME_MULT:
            continue

        # 5. Above 200 SMA
        if close <= sma200.iloc[i]:
            continue

        entry_price = close
        stop_price = low  # breakout bar low
        if stop_price >= entry_price:
            continue

        atr_val = atr.iloc[i]
        risk = entry_price - stop_price

        exit_info = _simulate_exit(df, i, entry_price, stop_price, atr_val)

        ts = pd.Timestamp(str(date))
        date_val = ts.date()

        signals.append(dict(
            ticker=ticker,
            date=date_val,
            entry_price=round(entry_price, 4),
            stop_price=round(stop_price, 4),
            target_price=None,  # no fixed target
            direction="long",
            subperiod=_subperiod(ts),
            strategy_id=STRATEGY_ID,
            **exit_info,
        ))

    return signals


if __name__ == "__main__":
    import sys
    test_ticker = "AAPL"
    cache_path = Path.home() / ".hermes" / "market_data" / f"{test_ticker}.parquet"
    if not cache_path.exists():
        print(f"[ERROR] Cache file not found: {cache_path}", file=sys.stderr)
        sys.exit(1)
    test_df = pd.read_parquet(cache_path)
    test_df.columns = test_df.columns.str.lower()
    print(f"Loaded {test_ticker}: {len(test_df)} bars  ({test_df.index[0]} -> {test_df.index[-1]})")
    results = scan(test_df, test_ticker)
    print(f"\nATR Contraction Breakout signals found: {len(results)}")
    if results:
        print("\nFirst 3 signals:")
        for sig in results[:3]:
            for k, v in sig.items():
                print(f"  {k:25s}: {v}")
            print()