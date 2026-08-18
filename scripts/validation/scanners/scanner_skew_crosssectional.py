#!/usr/bin/env python3
"""
scanner_skew_crosssectional.py — STR-SKEW: Cross-Sectional Return Skewness Factor

Built from CAND-20260818-skewness-cross-section.

Hypothesis (academic, Aug 2026 Journal of Investing + QuantPedia):
  Investors systematically overpay for lottery-like (high positive skew) return
  profiles and underprice crash-insurance-like (negative skew) assets. Sorting
  the cross-section on realized skewness and going long low-skew / short
  high-skew captures this premium as a standalone factor.

Signal Rules:
  1. At each rebalance date, compute 120-day rolling skewness of daily log
     returns for every asset in the universe.
  2. Rank assets cross-sectionally by skewness.
  3. Long the bottom quintile (most negative skew — crash-insurance premium).
  4. Short the top quintile (most positive skew — lottery-like, overpriced).
  5. Hold until next rebalance (weekly = 5 bars).
  6. Exit: stop loss at 2x ATR, or time stop at next rebalance.

This is a "batch" scanner — it takes the full data dict (stocks or crypto),
not a single ticker DataFrame.

Dependencies: pandas, numpy only.
"""

import numpy as np
import pandas as pd

STRATEGY_ID = "SKEW_CROSSSECTIONAL"

# ── Parameters (parameterizable for walk-forward optimization) ───────────────
SKEW_WINDOW = 120           # Rolling window for skewness computation (trading days)
REBALANCE_FREQ = 5          # Weekly rebalance (5 bars)
QUINTILE = 5                # Top/bottom quintile for long/short
ATR_PERIOD = 14             # ATR for stop placement
ATR_STOP_MULT = 2.0         # Stop = 2.0x ATR
MAX_BARS_HELD = 5           # Hold until next rebalance (time stop = rebalance)
MIN_ASSETS = 10             # Minimum assets with valid skewness to run


def _subperiod(date) -> str:
    """Classify a date into the ADR-004 sub-periods."""
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


def _compute_skewness(df: pd.DataFrame, date: pd.Timestamp,
                      window: int = SKEW_WINDOW) -> float:
    """
    Compute rolling skewness of daily log returns up to (and including) `date`.
    Returns np.nan if insufficient data.
    """
    mask = df.index <= date
    df_slice = df[mask]
    if len(df_slice) < window + 2:
        return np.nan

    close = df_slice["close"]
    log_returns = np.log(close / close.shift(1)).dropna()
    if len(log_returns) < window:
        return np.nan

    # Use the last `window` log returns
    window_returns = log_returns.iloc[-window:]
    if window_returns.std() == 0:
        return 0.0  # No variance → neutral skew

    return float(window_returns.skew())


def _simulate_exit(df: pd.DataFrame, entry_idx: int, direction: str,
                    entry_price: float, stop_price: float,
                    max_bars: int) -> tuple:
    """
    Simulate exit: stop loss or time stop.
    Returns (exit_price, exit_reason, bars_held).
    """
    closes = df["close"].values
    highs = df["high"].values
    lows = df["low"].values
    n = len(closes)

    for offset in range(1, max_bars + 1):
        idx = entry_idx + offset
        if idx >= n:
            return closes[min(entry_idx + offset - 1, n - 1)], "time", offset

        if direction == "long":
            if lows[idx] <= stop_price:
                return stop_price, "stop", offset
        else:
            if highs[idx] >= stop_price:
                return stop_price, "stop", offset

    exit_idx = min(entry_idx + max_bars, n - 1)
    return closes[exit_idx], "time", max_bars


def scan(data: dict) -> list:
    """
    Cross-sectional batch scanner. Takes the full data dict (stocks or crypto),
    ranks all tickers by rolling return skewness, and generates signals.

    Parameters
    ----------
    data : dict
        {ticker: DataFrame} mapping for all assets

    Returns
    -------
    list of dict, one per signal (long bottom-quintile, short top-quintile)
    """
    if not data or len(data) < MIN_ASSETS:
        return []

    # Collect all unique dates across all tickers
    all_dates = set()
    for df in data.values():
        all_dates.update(df.index)
    all_dates = sorted(all_dates)

    # Need enough history for skewness window
    min_start = SKEW_WINDOW + 5
    if len(all_dates) < min_start:
        return []

    # Start from the earliest date where skewness can be computed
    start_date = all_dates[min_start]
    all_dates = [d for d in all_dates if d >= start_date]

    # Rebalance dates (every REBALANCE_FREQ bars)
    rebalance_dates = all_dates[::REBALANCE_FREQ]

    signals = []

    for rebalance_idx, rebalance_date in enumerate(rebalance_dates):
        # Compute skewness for all tickers at this date
        skew_scores = {}
        for ticker, df in data.items():
            if len(df) < SKEW_WINDOW + 5:
                continue
            skew_val = _compute_skewness(df, rebalance_date)
            if not np.isnan(skew_val):
                skew_scores[ticker] = skew_val

        if len(skew_scores) < MIN_ASSETS:
            continue

        # Sort by skewness (ascending: most negative first)
        sorted_tickers = sorted(skew_scores.items(), key=lambda x: x[1])

        n = len(sorted_tickers)
        quintile_size = max(n // QUINTILE, 1)

        # Long bottom quintile (most negative skew — crash-insurance premium)
        # Short top quintile (most positive skew — lottery-like, overpriced)
        long_tickers = [t for t, _ in sorted_tickers[:quintile_size]]
        short_tickers = [t for t, _ in sorted_tickers[-quintile_size:]]

        # Next rebalance for time stop
        next_rebalance = (rebalance_dates[rebalance_idx + 1]
                          if rebalance_idx + 1 < len(rebalance_dates) else None)

        for ticker in long_tickers:
            sig = _create_signal(
                data, ticker, rebalance_date, "long",
                skew_scores[ticker], next_rebalance
            )
            if sig:
                signals.append(sig)

        for ticker in short_tickers:
            sig = _create_signal(
                data, ticker, rebalance_date, "short",
                skew_scores[ticker], next_rebalance
            )
            if sig:
                signals.append(sig)

    return signals


def _create_signal(data: dict, ticker: str, date: pd.Timestamp,
                    direction: str, skew_val: float,
                    next_rebalance: pd.Timestamp) -> dict:
    """
    Create a signal dict for a specific ticker at a rebalance date.
    Includes entry, stop, target, and simulated exit.
    """
    df = data.get(ticker)
    if df is None:
        return None

    mask = df.index <= date
    if mask.sum() < ATR_PERIOD + 5:
        return None

    df_slice = df[mask]
    entry_idx = len(df_slice) - 1
    entry_price = float(df_slice["close"].iloc[-1])

    # Compute ATR at entry
    atr = _compute_atr(df_slice)
    atr_val = float(atr.iloc[-1])

    if atr_val <= 0 or entry_price <= 0:
        return None

    if direction == "long":
        stop_price = entry_price - ATR_STOP_MULT * atr_val
        risk = entry_price - stop_price
        target_price = entry_price + 2 * risk
    else:
        stop_price = entry_price + ATR_STOP_MULT * atr_val
        risk = stop_price - entry_price
        target_price = entry_price - 2 * risk

    if risk <= 0:
        return None

    # Determine time stop
    max_bars = MAX_BARS_HELD
    if next_rebalance is not None:
        bars_after = (df.index > date).sum()
        if 0 < bars_after < 60:
            max_bars = min(max_bars, bars_after)

    # Simulate exit using full data
    exit_price, exit_reason, bars_held = _simulate_exit(
        df, entry_idx, direction, entry_price, stop_price, max_bars
    )

    # Compute R-multiple
    if direction == "long":
        realised_r = (exit_price - entry_price) / risk
    else:
        realised_r = (entry_price - exit_price) / risk

    return {
        "ticker": ticker,
        "date": date,
        "direction": direction,
        "entry_price": round(entry_price, 6),
        "stop_price": round(stop_price, 6),
        "target_price": round(target_price, 6),
        "exit_price": round(float(exit_price), 6),
        "exit_reason": exit_reason,
        "r_multiple": round(float(realised_r), 4),
        "bars_held": bars_held,
        "strategy_id": STRATEGY_ID,
        "skewness": round(skew_val, 4),
        "subperiod": _subperiod(date),
        "rebalance": True,
    }


if __name__ == "__main__":
    import sys
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "scripts" / "paper_trading"))
    from fetch_crypto_data import load_all as load_all_crypto

    print("Loading crypto data...")
    crypto = load_all_crypto()
    print(f"  {len(crypto)} symbols loaded")

    print("\nRunning STR-SKEW cross-sectional skewness ranking...")
    signals = scan(crypto)

    if not signals:
        print("No signals generated.")
        sys.exit(0)

    r_values = [s["r_multiple"] for s in signals]
    long_sigs = [s for s in signals if s["direction"] == "long"]
    short_sigs = [s for s in signals if s["direction"] == "short"]
    wins = [s for s in signals if s["r_multiple"] > 0]

    avg_r = np.mean(r_values)
    win_rate = len(wins) / len(signals)
    avg_win = np.mean([s["r_multiple"] for s in wins]) if wins else 0
    avg_loss = np.mean([s["r_multiple"] for s in signals if s["r_multiple"] <= 0]) or 0

    print(f"\nSTR-SKEW Phase 1A Results (Crypto):")
    print(f"  Signals: {len(signals)} ({len(long_sigs)} long, {len(short_sigs)} short)")
    print(f"  Avg R: {avg_r:+.4f}")
    print(f"  Win rate: {win_rate:.1%}")
    print(f"  Avg win: {avg_win:+.4f} | Avg loss: {avg_loss:+.4f}")

    # Long vs short
    long_r = [s["r_multiple"] for s in long_sigs]
    short_r = [s["r_multiple"] for s in short_sigs]
    print(f"\n  Long only:  {len(long_r):3d} sigs, avg R = {np.mean(long_r):+.4f}")
    print(f"  Short only: {len(short_r):3d} sigs, avg R = {np.mean(short_r):+.4f}")

    # By year
    by_year = {}
    for s in signals:
        yr = str(s["date"])[:4]
        by_year.setdefault(yr, []).append(s["r_multiple"])
    print(f"\n  By year:")
    for yr in sorted(by_year.keys()):
        yr_r = by_year[yr]
        print(f"    {yr}: {len(yr_r):3d} sigs, avg R = {np.mean(yr_r):+.4f}")
