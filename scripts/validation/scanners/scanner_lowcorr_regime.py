#!/usr/bin/env python3
"""
scanner_lowcorr_regime.py — STR-LOWCORR: Low-Correlation Regime Stock Picker

Built from CAND-20260814-low-correlation-regime.

Hypothesis:
  When the average pairwise correlation across the stock universe is low
  (< CORR_THRESHOLD), individual stock-specific edge matters more than
  market beta. This is a stock-picking environment where idiosyncratic
  strategies outperform. The scanner identifies the most idiosyncratic
  stocks (lowest average correlation to the market) and goes long them
  during low-correlation regimes.

Signal Rules:
  1. Compute 30-day rolling average pairwise correlation across the
     universe for each date.
  2. When avg correlation < CORR_THRESHOLD (0.30), enter "stock-picking"
     regime.
  3. Within the regime, rank stocks by their average correlation to the
     market proxy (equal-weighted universe). Long the bottom quintile
     (most idiosyncratic).
  4. Exit when correlation rises above EXIT_CORR (0.50) or after
     MAX_BARS_HELD (10 bars).
  5. Stop loss at 2x ATR.

This is a "batch" scanner — it takes the full stock data dict.

Dependencies: pandas, numpy only.
"""

import numpy as np
import pandas as pd

STRATEGY_ID = "LOWCORR_REGIME"

# ── Parameters (parameterizable for walk-forward optimization) ───────────────
CORR_WINDOW = 30            # Rolling window for correlation computation
CORR_THRESHOLD = 0.30        # Below this = low-correlation (stock-picking) regime
EXIT_CORR = 0.50             # Above this = exit regime
REBALANCE_FREQ = 5            # Rebalance every 5 bars (weekly)
QUINTILE = 5                  # Bottom quintile = most idiosyncratic
ATR_PERIOD = 14               # ATR for stop placement
ATR_STOP_MULT = 2.0           # Stop = 2.0x ATR
MAX_BARS_HELD = 10            # Time stop
MIN_ASSETS = 20               # Minimum assets for meaningful correlation matrix


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


def _compute_market_proxy(data: dict, dates: pd.DatetimeIndex) -> pd.Series:
    """
    Compute equal-weighted market return series from all tickers' daily returns.
    Returns a Series of daily returns indexed by date.
    """
    all_returns = []
    for ticker, df in data.items():
        if len(df) < CORR_WINDOW + 5:
            continue
        rets = df["close"].pct_change()
        rets.name = ticker
        all_returns.append(rets)

    if not all_returns:
        return pd.Series(dtype=float)

    # Align on common dates
    ret_df = pd.concat(all_returns, axis=1)
    market_ret = ret_df.mean(axis=1)  # equal-weighted average
    return market_ret


def _compute_avg_correlation(data: dict, date: pd.Timestamp,
                              corr_window: int = CORR_WINDOW) -> tuple:
    """
    Compute the average pairwise correlation across the universe at a given date.
    Returns (avg_corr, per_ticker_corr_to_market) where the latter is
    {ticker: correlation_to_market_proxy}.

    Uses the last `corr_window` bars of returns up to `date`.

    Optimized: pre-extracts returns as a numpy matrix and uses np.corrcoef
    instead of building a DataFrame and calling .corr() per-ticker.
    """
    # Collect returns for all tickers in the window
    tickers = []
    ret_arrays = []
    for ticker, df in data.items():
        mask = df.index <= date
        df_slice = df[mask]
        if len(df_slice) < corr_window + 2:
            continue
        rets = df_slice["close"].pct_change().dropna().values
        if len(rets) < corr_window:
            continue
        tickers.append(ticker)
        ret_arrays.append(rets[-corr_window:])

    if len(tickers) < MIN_ASSETS:
        return np.nan, {}

    # Build returns matrix: shape (n_tickers, corr_window)
    ret_matrix = np.array(ret_arrays, dtype=np.float64)

    # Drop columns (time steps) where any ticker has NaN
    valid_cols = ~np.isnan(ret_matrix).any(axis=0)
    ret_matrix = ret_matrix[:, valid_cols]
    n_tickers = ret_matrix.shape[0]

    if n_tickers < MIN_ASSETS or ret_matrix.shape[1] < 2:
        return np.nan, {}

    # Market proxy = equal-weighted average of all returns
    market_ret = ret_matrix.mean(axis=0)

    # Correlation of each ticker to market proxy (vectorized)
    # Stack: [tickers; market] -> corrcoef -> extract last row
    stacked = np.vstack([ret_matrix, market_ret])
    corr_matrix_full = np.corrcoef(stacked)
    corr_to_market_vals = corr_matrix_full[-1, :-1]

    corr_to_market = {}
    for i, ticker in enumerate(tickers):
        c = corr_to_market_vals[i]
        if not np.isnan(c):
            corr_to_market[ticker] = float(c)

    # Average pairwise correlation: use the ticker-only correlation matrix
    corr_matrix = corr_matrix_full[:-1, :-1]

    # Extract upper triangle (excluding diagonal)
    mask_upper = np.triu(np.ones(corr_matrix.shape, dtype=bool), k=1)
    upper_vals = corr_matrix[mask_upper]
    upper_vals = upper_vals[~np.isnan(upper_vals)]

    if len(upper_vals) == 0:
        return np.nan, corr_to_market

    avg_corr = float(np.mean(upper_vals))
    return avg_corr, corr_to_market


def _simulate_exit(df: pd.DataFrame, entry_idx: int, direction: str,
                    entry_price: float, stop_price: float,
                    max_bars: int) -> tuple:
    """Simulate exit: stop loss or time stop."""
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


def scan(data: dict, latest_only: bool = False) -> list:
    """
    Batch scanner. Takes the full stock data dict, identifies low-correlation
    regime periods, and generates long signals for the most idiosyncratic stocks.

    Parameters
    ----------
    data : dict
        {ticker: DataFrame} mapping for all stock tickers
    latest_only : bool
        If True, only evaluate the most recent rebalance date (for live
        signal capture — avoids computing 300+ historical correlation
        matrices that will be discarded). Default False (full backtest).

    Returns
    -------
    list of dict, one per signal (long bottom-quintile by idiosyncrasy)
    """
    if not data or len(data) < MIN_ASSETS:
        return []

    # Collect all unique dates
    all_dates = set()
    for df in data.values():
        all_dates.update(df.index)
    all_dates = sorted(all_dates)

    # Need enough history for correlation window
    min_start = CORR_WINDOW + 10
    if len(all_dates) < min_start:
        return []

    start_date = all_dates[min_start]
    all_dates = [d for d in all_dates if d >= start_date]

    # Rebalance dates
    rebalance_dates = all_dates[::REBALANCE_FREQ]

    # Live capture: only evaluate the most recent rebalance
    if latest_only and rebalance_dates:
        rebalance_dates = [rebalance_dates[-1]]

    signals = []
    in_regime = False

    for rebalance_idx, rebalance_date in enumerate(rebalance_dates):
        # Compute correlation regime at this date
        avg_corr, corr_to_market = _compute_avg_correlation(data, rebalance_date)

        if np.isnan(avg_corr) or len(corr_to_market) < MIN_ASSETS:
            in_regime = False
            continue

        # Check regime entry/exit
        if avg_corr < CORR_THRESHOLD:
            in_regime = True
        elif avg_corr > EXIT_CORR:
            in_regime = False

        if not in_regime:
            continue

        # Sort by correlation to market (ascending = most idiosyncratic first)
        sorted_tickers = sorted(corr_to_market.items(), key=lambda x: x[1])

        n = len(sorted_tickers)
        quintile_size = max(n // QUINTILE, 1)

        # Long the bottom quintile (most idiosyncratic = lowest corr to market)
        long_tickers = [t for t, _ in sorted_tickers[:quintile_size]]

        next_rebalance = (rebalance_dates[rebalance_idx + 1]
                          if rebalance_idx + 1 < len(rebalance_dates) else None)

        for ticker in long_tickers:
            sig = _create_signal(
                data, ticker, rebalance_date, "long",
                corr_to_market[ticker], avg_corr, next_rebalance
            )
            if sig:
                signals.append(sig)

    return signals


def _create_signal(data: dict, ticker: str, date: pd.Timestamp,
                    direction: str, corr_val: float, avg_corr: float,
                    next_rebalance: pd.Timestamp) -> dict:
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

    # Time stop
    max_bars = MAX_BARS_HELD
    if next_rebalance is not None:
        bars_after = (df.index > date).sum()
        if 0 < bars_after < 60:
            max_bars = min(max_bars, bars_after)

    # Simulate exit
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
        "corr_to_market": round(corr_val, 4),
        "avg_universe_corr": round(avg_corr, 4),
        "subperiod": _subperiod(date),
        "rebalance": True,
    }


if __name__ == "__main__":
    import sys
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "scripts" / "validation"))
    from fetch_data import load_all as load_all_stocks

    print("Loading stock data...")
    stocks = load_all_stocks()
    print(f"  {len(stocks)} tickers loaded")

    print("\nRunning STR-LOWCORR low-correlation regime scanner...")
    signals = scan(stocks)

    if not signals:
        print("No signals generated.")
        sys.exit(0)

    r_values = [s["r_multiple"] for s in signals]
    wins = [s for s in signals if s["r_multiple"] > 0]

    avg_r = np.mean(r_values)
    win_rate = len(wins) / len(signals)
    avg_win = np.mean([s["r_multiple"] for s in wins]) if wins else 0
    avg_loss = np.mean([s["r_multiple"] for s in signals if s["r_multiple"] <= 0]) or 0

    print(f"\nSTR-LOWCORR Phase 1A Results (Stocks):")
    print(f"  Signals: {len(signals)}")
    print(f"  Avg R: {avg_r:+.4f}")
    print(f"  Win rate: {win_rate:.1%}")
    print(f"  Avg win: {avg_win:+.4f} | Avg loss: {avg_loss:+.4f}")

    # By year
    by_year = {}
    for s in signals:
        yr = str(s["date"])[:4]
        by_year.setdefault(yr, []).append(s["r_multiple"])
    print(f"\n  By year:")
    for yr in sorted(by_year.keys()):
        yr_r = by_year[yr]
        print(f"    {yr}: {len(yr_r):3d} sigs, avg R = {np.mean(yr_r):+.4f}")
