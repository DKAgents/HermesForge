"""
scanner_gold_collapse_equity_leading.py — STR-GOLD-LEAD: Gold Collapse as Leading Indicator for Equities

Built from CAND-20260830-gold-collapse-risk-signal.

Hypothesis:
  When GLD drops >2.5% in a single day while SPY is flat/positive (>-0.5%),
  SPY tends to follow lower within 1-10 trading days. Gold is a "canary in
  the coal mine" — forced selling in hard assets (margin calls, dollar
  strength) precedes equity weakness.

Signal Rules:
  1. Compute GLD daily return < -2.5%
  2. SPY daily return > -0.5% (equity complacency)
  3. Generate SHORT signal on SPY when both conditions are met
  4. Exit: target hit, stop hit, or max 10 bars

This is a "batch" scanner — it takes the full stock data dict.

Dependencies: pandas, numpy only.
"""

import numpy as np
import pandas as pd

STRATEGY_ID = "STR-GOLD-LEAD"

# ── Parameters (parameterizable for walk-forward optimization) ───────────────
GLD_DROP_PCT = 2.5           # GLD must drop more than this % (positive value, check < -pct)
SPY_FLAT_THRESHOLD = 0.5    # SPY return must be > -this % (i.e., flat to up)
ATR_PERIOD = 14
ATR_STOP_MULT = 0.8
MIN_RR = 1.5
MAX_HOLD = 10


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


def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                  period: int = ATR_PERIOD) -> pd.Series:
    """Average True Range (Wilder's smoothing)."""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _simulate_exit(
    closes: np.ndarray,
    entry_idx: int,
    entry_price: float,
    stop_price: float,
    target_price: float,
    direction: str,
    max_bars: int = MAX_HOLD,
) -> tuple:
    """Simulate forward exit scan. Short direction."""
    n = len(closes)
    for offset in range(1, max_bars + 1):
        idx = entry_idx + offset
        if idx >= n:
            last = min(entry_idx + offset - 1, n - 1)
            return closes[last], "time", offset
        c = closes[idx]
        if direction == "short":
            if c <= target_price:
                return c, "target", offset
            if c >= stop_price:
                return c, "stop", offset
        else:
            if c >= target_price:
                return c, "target", offset
            if c <= stop_price:
                return c, "stop", offset
    exit_idx = min(entry_idx + max_bars, n - 1)
    return closes[exit_idx], "time", max_bars


def scan(data: dict[str, pd.DataFrame]) -> list[dict]:
    """
    Batch scanner: checks GLD vs SPY divergence and generates SPY short signals.

    Parameters
    ----------
    data : dict[str, pd.DataFrame]
        Dict of {ticker: OHLCV DataFrame} for the stock universe.

    Returns
    -------
    list of dict, one per signal
    """
    needed = {"GLD", "SPY"}
    available = set(data.keys())
    missing = needed - available
    if missing:
        raise ValueError(f"Missing tickers in data dict: {missing}")

    gld = data["GLD"].copy()
    spy = data["SPY"].copy()

    # Normalize columns
    for df in [gld, spy]:
        df.columns = df.columns.str.lower()
        df.sort_index(inplace=True)

    gld_close = gld["close"]
    spy_close = spy["close"]
    spy_high = spy["high"]
    spy_low = spy["low"]

    # Compute daily returns
    gld_ret = gld_close.pct_change() * 100  # percentage
    spy_ret = spy_close.pct_change() * 100

    # ATR for SPY
    spy_atr = _compute_atr(spy_high, spy_low, spy_close, period=ATR_PERIOD)

    # Align indices (inner join on common dates)
    common_dates = gld_ret.index.intersection(spy_ret.index)
    gld_ret = gld_ret.loc[common_dates]
    spy_ret = spy_ret.loc[common_dates]
    spy_close_aligned = spy_close.loc[common_dates]
    spy_atr_aligned = spy_atr.loc[common_dates]
    spy_high_aligned = spy_high.loc[common_dates]
    spy_low_aligned = spy_low.loc[common_dates]

    spy_close_arr = spy_close_aligned.values.astype(float)
    spy_high_arr = spy_high_aligned.values.astype(float)
    spy_atr_arr = spy_atr_aligned.values.astype(float)
    gld_ret_arr = gld_ret.values.astype(float)
    spy_ret_arr = spy_ret.values.astype(float)

    signals: list[dict] = []

    # Need at least ATR_PERIOD + 2 bars for ATR warmup + return computation
    min_start = ATR_PERIOD + 2

    for i in range(min_start, len(common_dates)):
        # Check for NaN in indicators
        if (np.isnan(gld_ret_arr[i]) or np.isnan(spy_ret_arr[i]) or
                np.isnan(spy_atr_arr[i])):
            continue

        # Signal condition: GLD drops > GLD_DROP_PCT % AND SPY is flat/positive
        if gld_ret_arr[i] < -GLD_DROP_PCT and spy_ret_arr[i] > -SPY_FLAT_THRESHOLD:
            entry_price = spy_close_arr[i]
            if entry_price == 0 or np.isnan(entry_price):
                continue

            atr_val = spy_atr_arr[i]
            if atr_val == 0 or np.isnan(atr_val):
                continue

            # Short SPY
            stop_price = spy_high_arr[i] + ATR_STOP_MULT * atr_val
            risk = stop_price - entry_price
            if risk <= 0:
                continue

            reward = 2.0 * risk  # 2:1 reward-to-risk
            target_price = entry_price - reward
            rr = reward / risk
            if rr < MIN_RR:
                continue

            ep, er, bh = _simulate_exit(
                spy_close_arr, i, entry_price, stop_price, target_price, "short"
            )
            r_mult = (entry_price - ep) / risk
            ts = pd.Timestamp(str(common_dates[i]))

            signals.append({
                "ticker":       "SPY",
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
# __main__ : quick smoke test
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Test with cached data
    from fetch_data import load_all
    print("Loading cached stock data...")
    stock_data = load_all()
    if not stock_data:
        print("ERROR: No cached data. Run with --fetch first.", file=sys.stderr)
        sys.exit(1)
    print(f"Loaded {len(stock_data)} tickers.")

    results = scan(stock_data)
    print(f"\nGold Collapse signals found: {len(results)}")
    if results:
        print("\nFirst 3 signals:")
        for sig in results[:3]:
            for k, v in sig.items():
                print(f"  {k:25s}: {v}")
            print()