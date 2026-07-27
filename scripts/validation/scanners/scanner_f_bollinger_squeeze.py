"""
scanner_f_bollinger_squeeze.py
Strategy F — Bollinger Band Squeeze Breakout

Entry logic (bidirectional):
  - Bollinger Bands: 20-period SMA, +/- 2 standard deviations (population
    std, ddof=0) of close over the same 20-period window.
  - Band width = (upper_band - lower_band) / middle_band (normalized width).
  - Squeeze condition: today's band width is the LOWEST value in the
    trailing 60-bar window (band_width.iloc[i] == band_width.iloc[i-59:i+1].min())
    -- identifies volatility compression.
  - LONG signal  : squeeze condition true on bar i-1 (yesterday was the
                   squeeze low) AND today's close breaks above yesterday's
                   upper band value.
  - SHORT signal : squeeze condition true on bar i-1 AND today's close
                   breaks below yesterday's lower band value.
  - Volume filter: today's volume >= 1.2x the 20-bar average volume
                   (same volume-ratio pattern as scanner_c_breakout_volume.py).
  - Entry price  = close of breakout bar.
  - Stop price (long)  = lower_band value from the breakout bar (today's
                          lower band).
  - Stop price (short) = upper_band value from the breakout bar (today's
                          upper band).
    (Uses the band width itself as the risk unit.)
  - Target price = entry +/- 2x(entry - stop) for longs /
                    2x(stop - entry) for shorts (2:1 R:R projection).

Filters:
  - Skip if R:R < 2.0
  - Skip if stop == entry

Exit simulation (forward scan up to 10 bars):
  - 'target' : hit target_price first
  - 'stop'   : hit stop_price first
  - 'time'   : neither hit within 10 bars

Output fields per signal:
  ticker, date, entry_price, stop_price, target_price, direction,
  exit_price, exit_reason, bars_held, r_multiple, subperiod, strategy_id,
  volume_ratio, band_width

Dependencies: pandas, numpy only.
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID    = "STR-F-bollinger-squeeze-breakout"
BB_PERIOD      = 20         # bars for SMA / std dev
BB_STD_MULT    = 2.0        # band width multiplier
SQUEEZE_WINDOW = 60         # trailing bars for squeeze-low detection
VOLUME_MULT    = 1.2        # volume confirmation multiplier
MIN_RR         = 2.0        # minimum reward-to-risk ratio
MAX_HOLD       = 10         # maximum bars to hold (time stop)
LOOKBACK       = 60          # per spec: scan loop can start at index >= 60


def _subperiod(date: "pd.Timestamp | pd.NaTType") -> str:  # type: ignore[name-defined]
    """Assign a calendar sub-period label (quarter) to a date."""
    ts = pd.Timestamp(str(date))
    return f"{ts.year}-Q{ts.quarter}"


def _simulate_exit(
    df: pd.DataFrame,
    entry_idx: int,
    entry_price: float,
    stop_price: float,
    target_price: float,
    direction: str,
) -> dict:
    """
    Walk forward from the bar *after* entry for up to MAX_HOLD bars.
    For 'long'  : target = close >= target_price ; stop = close <= stop_price
    For 'short' : target = close <= target_price ; stop = close >= stop_price
    Returns a dict with exit_price, exit_reason, bars_held, r_multiple.
    """
    if direction == "long":
        risk = entry_price - stop_price  # > 0 guaranteed by caller
    else:
        risk = stop_price - entry_price  # > 0 guaranteed by caller

    n = len(df)

    for offset in range(1, MAX_HOLD + 1):
        bar_idx = entry_idx + offset
        if bar_idx >= n:
            last_close = df["close"].iloc[bar_idx - 1] if bar_idx > 0 else entry_price
            if direction == "long":
                r_mult = (last_close - entry_price) / risk
            else:
                r_mult = (entry_price - last_close) / risk
            return dict(
                exit_price  = round(float(last_close), 4),
                exit_reason = "time",
                bars_held   = offset,
                r_multiple  = round(float(r_mult), 3),
            )

        close = df["close"].iloc[bar_idx]

        if direction == "long":
            # Check stop first (protects capital)
            if close <= stop_price:
                r_mult = (close - entry_price) / risk
                return dict(
                    exit_price  = round(float(close), 4),
                    exit_reason = "stop",
                    bars_held   = offset,
                    r_multiple  = round(float(r_mult), 3),
                )
            if close >= target_price:
                r_mult = (close - entry_price) / risk
                return dict(
                    exit_price  = round(float(close), 4),
                    exit_reason = "target",
                    bars_held   = offset,
                    r_multiple  = round(float(r_mult), 3),
                )
        else:  # short
            if close >= stop_price:
                r_mult = (entry_price - close) / risk
                return dict(
                    exit_price  = round(float(close), 4),
                    exit_reason = "stop",
                    bars_held   = offset,
                    r_multiple  = round(float(r_mult), 3),
                )
            if close <= target_price:
                r_mult = (entry_price - close) / risk
                return dict(
                    exit_price  = round(float(close), 4),
                    exit_reason = "target",
                    bars_held   = offset,
                    r_multiple  = round(float(r_mult), 3),
                )

    # Time stop: neither target nor stop hit within MAX_HOLD bars
    last_close = df["close"].iloc[entry_idx + MAX_HOLD]
    if direction == "long":
        r_mult = (last_close - entry_price) / risk
    else:
        r_mult = (entry_price - last_close) / risk
    return dict(
        exit_price  = round(float(last_close), 4),
        exit_reason = "time",
        bars_held   = MAX_HOLD,
        r_multiple  = round(float(r_mult), 3),
    )


def scan(df: pd.DataFrame, ticker: str) -> list[dict]:
    """
    Scan a price DataFrame for Strategy F — Bollinger Band Squeeze Breakout
    signals (both directions).

    Parameters
    ----------
    df     : DataFrame with columns [open, high, low, close, volume]
             sorted chronologically (oldest first), DatetimeIndex.
    ticker : Ticker symbol string (for output labelling).

    Returns
    -------
    List of signal dicts, one per triggered bar.
    """
    df = df.copy()
    df.columns = df.columns.str.lower()
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(df.columns):
        raise ValueError(f"DataFrame missing columns: {required - set(df.columns)}")
    df.sort_index(inplace=True)

    close  = df["close"]
    volume = df["volume"]

    # --- Compute Bollinger Bands ---
    sma       = close.rolling(window=BB_PERIOD).mean()
    std       = close.rolling(window=BB_PERIOD).std(ddof=0)
    upper_band = sma + BB_STD_MULT * std
    lower_band = sma - BB_STD_MULT * std
    band_width = (upper_band - lower_band) / sma

    # --- Squeeze condition: today's band width is the lowest in trailing 60 bars ---
    squeeze_min = band_width.rolling(window=SQUEEZE_WINDOW).min()
    is_squeeze  = band_width == squeeze_min

    # --- Volume baseline (20-bar average, matching band period) ---
    avg_volume = volume.rolling(window=BB_PERIOD).mean()

    signals: list[dict] = []

    for i in range(LOOKBACK, len(df)):
        # Need bar i-1's squeeze condition and band values
        if i - 1 < 0:
            continue

        squeeze_yesterday = is_squeeze.iloc[i - 1]
        if pd.isna(squeeze_yesterday) or not bool(squeeze_yesterday):
            continue

        upper_yesterday = upper_band.iloc[i - 1]
        lower_yesterday = lower_band.iloc[i - 1]
        if pd.isna(upper_yesterday) or pd.isna(lower_yesterday):
            continue

        today_close  = close.iloc[i]
        today_volume = volume.iloc[i]
        avg_vol_i    = avg_volume.iloc[i]

        if pd.isna(avg_vol_i) or avg_vol_i <= 0:
            continue

        volume_ratio = today_volume / avg_vol_i
        if volume_ratio < VOLUME_MULT:
            continue

        direction = None
        if today_close > upper_yesterday:
            direction = "long"
        elif today_close < lower_yesterday:
            direction = "short"
        else:
            continue

        today_upper = upper_band.iloc[i]
        today_lower = lower_band.iloc[i]
        if pd.isna(today_upper) or pd.isna(today_lower):
            continue

        entry_price = float(today_close)

        if direction == "long":
            stop_price = float(today_lower)
            if stop_price >= entry_price:
                continue
            risk         = entry_price - stop_price
            target_price = entry_price + 2.0 * risk
        else:
            stop_price = float(today_upper)
            if stop_price <= entry_price:
                continue
            risk         = stop_price - entry_price
            target_price = entry_price - 2.0 * risk

        if risk <= 0:
            continue

        reward = abs(target_price - entry_price)
        rr = reward / risk
        if rr < MIN_RR:
            continue

        exit_info = _simulate_exit(df, i, entry_price, stop_price, target_price, direction)

        raw_date = df.index[i]
        ts       = pd.Timestamp(str(raw_date))
        date_val = ts.date()

        signals.append(dict(
            ticker       = ticker,
            date         = date_val,
            entry_price  = round(entry_price, 4),
            stop_price   = round(stop_price, 4),
            target_price = round(target_price, 4),
            direction    = direction,
            subperiod    = _subperiod(ts),
            strategy_id  = STRATEGY_ID,
            volume_ratio = round(float(volume_ratio), 4),
            band_width   = round(float(band_width.iloc[i]), 6),
            **exit_info,
        ))

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
    print(f"Loaded SPY: {len(spy_df)} bars  ({spy_df.index[0]} → {spy_df.index[-1]})")

    results = scan(spy_df, "SPY")
    print(f"\nStrategy F signals found: {len(results)}")

    if results:
        print("\nFirst 3 signals:")
        for sig in results[:3]:
            for k, v in sig.items():
                print(f"  {k:25s}: {v}")
            print()
