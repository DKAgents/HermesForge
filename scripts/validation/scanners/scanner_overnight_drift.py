#!/usr/bin/env python3
"""
scanner_overnight_drift.py — STR-OVNIGHT: Overnight (Close-to-Open) Drift Factor

Edge candidate: CAND-20260820-overnight-drift-factor
Source hypothesis: Decompose each asset's daily return into overnight
(open_t / close_{t-1} − 1) and intraday (close_t / open_t − 1) components.
Assets with the strongest positive cumulative overnight drift carry a premium
distinct from momentum, reversal, and volatility factors.

This is a batch scanner (like scanner_p_crosssectional): it takes the full
stock data dict, ranks all tickers cross-sectionally on rolling cumulative
overnight return, and generates long signals for the top quintile and short
signals for the bottom quintile.

Signal Rules:
  1. At each rebalance date, compute rolling cumulative overnight return
     for all tickers (product of daily overnight returns over the lookback).
  2. Rank tickers cross-sectionally by overnight drift.
  3. Long top quintile, short bottom quintile.
  4. Hold until next rebalance (monthly = 21 bars).
  5. Exit: stop loss at ATR_STOP_MULT × ATR, or time stop at next rebalance.

Dependencies: pandas, numpy only.
Survivorship-bias caveat: universe is current S&P constituents (ADR-004).
"""

import numpy as np
import pandas as pd

STRATEGY_ID = "STR-OVNIGHT-DRIFT"

# ── Parameters (module-level so walk-forward can monkey-patch) ───────────────
REBALANCE_FREQ = 21          # Rebalance every 21 bars (monthly)
QUINTILE = 5                 # Top/bottom quintile for long/short
ATR_PERIOD = 14              # ATR for stop placement
ATR_STOP_MULT = 1.5          # Stop = 1.5x ATR
MAX_BARS_HELD = 21           # Hold until next rebalance (time stop)
MIN_RR = 1.0                 # Minimum R:R (relaxed — factor ranking is the edge)
DRIFT_LOOKBACK = 60          # Rolling window for cumulative overnight return


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


def _compute_overnight_returns(df: pd.DataFrame) -> pd.Series:
    """Compute daily overnight return: open_t / close_{t-1} - 1."""
    close_prev = df["close"].shift(1)
    overnight = df["open"] / close_prev - 1.0
    return overnight


def _compute_cumulative_overnight_drift(df: pd.DataFrame, date: pd.Timestamp,
                                          lookback: int = DRIFT_LOOKBACK) -> float:
    """
    Compute cumulative overnight return over the rolling lookback window
    ending at `date`. Returns the product of (1 + overnight) - 1.
    """
    mask = df.index <= date
    df_slice = df[mask]
    if len(df_slice) < lookback + 2:
        return np.nan

    overnight = _compute_overnight_returns(df_slice)
    # Take the last `lookback` values
    recent = overnight.iloc[-lookback:]
    if len(recent) < lookback or recent.isna().any():
        # Allow up to 10% NaN by filling with 0
        if recent.isna().sum() > lookback * 0.1:
            return np.nan
        recent = recent.fillna(0.0)

    cumulative = float(np.prod(1.0 + recent.values) - 1.0)
    return cumulative


def _compute_factor_scores(data: dict, date: pd.Timestamp) -> dict:
    """
    Compute overnight drift factor scores for all tickers at a specific date.
    Returns {ticker: {"drift": value, "drift_z": z_score}} dict.
    """
    factor_values = {}

    for ticker, df in data.items():
        if len(df) < DRIFT_LOOKBACK + 10:
            continue

        mask = df.index <= date
        if mask.sum() < DRIFT_LOOKBACK + 2:
            continue

        drift = _compute_cumulative_overnight_drift(df, date, DRIFT_LOOKBACK)
        if np.isnan(drift):
            continue

        factor_values[ticker] = {"drift": drift}

    if len(factor_values) < QUINTILE:
        return {}

    # Convert to z-scores (cross-sectional standardization)
    values = [fv["drift"] for fv in factor_values.values()]
    mean = np.mean(values)
    std = np.std(values)
    if std > 0:
        for ticker in factor_values:
            factor_values[ticker]["drift_z"] = (
                factor_values[ticker]["drift"] - mean
            ) / std
    else:
        for ticker in factor_values:
            factor_values[ticker]["drift_z"] = 0.0

    return factor_values


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


def _create_signal(data: dict, ticker: str, date: pd.Timestamp,
                    direction: str, factor_scores: dict,
                    next_rebalance) -> dict:
    """Create a signal dict for a specific ticker at a rebalance date."""
    df = data.get(ticker)
    if df is None:
        return None

    mask = df.index <= date
    if mask.sum() < ATR_PERIOD + 5:
        return None

    df_slice = df[mask]
    entry_idx = len(df_slice) - 1
    entry_price = float(df_slice["close"].iloc[-1])

    atr = _compute_atr(df_slice)
    atr_val = float(atr.iloc[-1])

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

    # Determine time stop (next rebalance or MAX_BARS_HELD)
    max_bars = MAX_BARS_HELD
    if next_rebalance is not None:
        bars_to_next = (df.index > date).sum()
        if 0 < bars_to_next < 60:
            max_bars = bars_to_next

    # Simulate exit using full data (not just slice)
    exit_price, exit_reason, bars_held = _simulate_exit(
        df, entry_idx, direction, entry_price, stop_price, max_bars
    )

    # Compute R-multiple
    if direction == "long":
        realised_r = (exit_price - entry_price) / risk
    else:
        realised_r = (entry_price - exit_price) / risk

    # Sub-period labeling
    d = date
    if hasattr(d, 'date'):
        d = d.date()
    if d < pd.Timestamp("2019-04-01").date():
        subperiod = "pre_warmup"
    elif d <= pd.Timestamp("2021-12-31").date():
        subperiod = "period1_bull"
    elif d <= pd.Timestamp("2023-12-31").date():
        subperiod = "period2_bear"
    else:
        subperiod = "period3_current"

    return {
        "ticker": ticker,
        "date": date,
        "direction": direction,
        "entry_price": round(entry_price, 4),
        "stop_price": round(stop_price, 4),
        "target_price": round(target_price, 4),
        "exit_price": round(float(exit_price), 4),
        "exit_reason": exit_reason,
        "r_multiple": round(float(realised_r), 4),
        "bars_held": bars_held,
        "strategy_id": STRATEGY_ID,
        "overnight_drift": round(factor_scores.get("drift", 0), 4),
        "drift_z": round(factor_scores.get("drift_z", 0), 4),
        "subperiod": subperiod,
        "rebalance": True,
    }


def scan(data: dict) -> list:
    """
    Cross-sectional batch scanner. Takes the full stock data dict,
    ranks all tickers by cumulative overnight drift, and generates signals.

    Parameters
    ----------
    data : dict
        {ticker: DataFrame} mapping for all stock symbols

    Returns
    -------
    list of dict, one per signal (long top quintile, short bottom quintile)
    """
    if not data or len(data) < QUINTILE:
        return []

    # Get all unique dates
    all_dates = set()
    for df in data.values():
        all_dates.update(df.index)
    all_dates = sorted(all_dates)

    # Start from the earliest date where all factors can be computed
    min_start = DRIFT_LOOKBACK + 10
    if len(all_dates) < min_start:
        return []

    first_benchmark = list(data.values())[0]
    start_date = first_benchmark.index[min_start] if len(first_benchmark) > min_start else all_dates[min_start]
    all_dates = [d for d in all_dates if d >= start_date]

    # Rebalance dates
    rebalance_dates = all_dates[::REBALANCE_FREQ]

    signals = []

    for rebalance_idx, rebalance_date in enumerate(rebalance_dates):
        # Compute factor scores at this date
        factor_scores = _compute_factor_scores(data, rebalance_date)
        if len(factor_scores) < QUINTILE:
            continue

        # Sort by overnight drift z-score (highest = most positive drift)
        sorted_tickers = sorted(
            factor_scores.items(),
            key=lambda x: x[1]["drift_z"],
            reverse=True
        )

        n = len(sorted_tickers)
        quintile_size = n // QUINTILE
        if quintile_size < 1:
            continue

        # Long top quintile (highest overnight drift), short bottom quintile
        long_tickers = [t for t, _ in sorted_tickers[:quintile_size]]
        short_tickers = [t for t, _ in sorted_tickers[-quintile_size:]]

        # Find the next rebalance date for time stop
        next_rebalance = rebalance_dates[rebalance_idx + 1] if rebalance_idx + 1 < len(rebalance_dates) else None

        for ticker in long_tickers:
            sig = _create_signal(
                data, ticker, rebalance_date, "long",
                factor_scores[ticker], next_rebalance
            )
            if sig:
                signals.append(sig)

        for ticker in short_tickers:
            sig = _create_signal(
                data, ticker, rebalance_date, "short",
                factor_scores[ticker], next_rebalance
            )
            if sig:
                signals.append(sig)

    return signals


if __name__ == "__main__":
    import sys
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
    from fetch_data import load_all

    print("Loading stock data...")
    stocks = load_all()
    print(f"  {len(stocks)} tickers loaded")

    print("\nRunning STR-OVNIGHT overnight drift factor ranking...")
    signals = scan(stocks)

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
    pf = sum(max(r, 0) for r in r_values) / max(abs(sum(min(r, 0) for r in r_values)), 0.01)

    print(f"\nSTR-OVNIGHT Phase 1A Results (Stocks):")
    print(f"  Signals: {len(signals)} ({len(long_sigs)} long, {len(short_sigs)} short)")
    print(f"  Avg R: {avg_r:+.4f}")
    print(f"  Win rate: {win_rate:.1%}")
    print(f"  Avg win: {avg_win:+.4f} | Avg loss: {avg_loss:+.4f}")
    print(f"  Profit factor: {pf:.2f}")

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
        print(f"    {yr}: {len(yr_r):3d} sigs, avg R = {np.mean(yr_r):+.4f}")

    # Long vs short
    long_r = [s["r_multiple"] for s in long_sigs]
    short_r = [s["r_multiple"] for s in short_sigs]
    print(f"\n  Long only:  {len(long_r):3d} sigs, avg R = {np.mean(long_r):+.4f}")
    print(f"  Short only: {len(short_r):3d} sigs, avg R = {np.mean(short_r):+.4f}")
