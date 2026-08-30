"""
scanner_nvda_breakdown_market_risk.py — STR-NVDA-LEAD: NVDA Breakdown as Market Structure Risk

Built from CAND-20260830-nvda-breakdown-market-risk.

Hypothesis:
  NVDA daily drops >3.5% predict SPY/QQQ weakness within 1-5 days.
  As the largest single stock (~7% of SPY), NVVA's breakdown signals
  broad risk appetite leaving the market, particularly from the AI/semi
  trade that has been the primary market narrative.

Signal Rules:
  1. Compute NVDA daily return < -3.5%
  2. Generate SHORT signal on SPY when triggered
  3. Volume confirmation: NVDA volume > 1.2x 20d average (optional filter)
  4. Exit: target hit, stop hit, or max 5 bars

This is a "batch" scanner — it takes the full stock data dict.

Dependencies: pandas, numpy only.
"""

import numpy as np
import pandas as pd

STRATEGY_ID = "STR-NVDA-LEAD"

# ── Parameters (parameterizable for walk-forward optimization) ───────────────
NVDA_DROP_PCT = 3.5          # NVDA must drop more than this %
VOLUME_MULT = 1.2            # Volume must be > 1.2x 20d average
ATR_PERIOD = 14
ATR_STOP_MULT = 0.8
MIN_RR = 1.5
MAX_HOLD = 5                 # Shorter max hold — rapid response signal


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
    Batch scanner: checks NVDA breakdown and generates SPY short signals.

    Parameters
    ----------
    data : dict[str, pd.DataFrame]
        Dict of {ticker: OHLCV DataFrame} for the stock universe.

    Returns
    -------
    list of dict, one per signal
    """
    needed = {"NVDA", "SPY"}
    available = set(data.keys())
    missing = needed - available
    if missing:
        raise ValueError(f"Missing tickers in data dict: {missing}")

    nvda = data["NVDA"].copy()
    spy = data["SPY"].copy()

    # Normalize columns
    for df in [nvda, spy]:
        df.columns = df.columns.str.lower()
        df.sort_index(inplace=True)

    nvda_close = nvda["close"]
    nvda_volume = nvda["volume"]
    spy_close = spy["close"]
    spy_high = spy["high"]

    # Compute daily returns
    nvda_ret = nvda_close.pct_change() * 100

    # Volume MA
    nvda_vol_ma20 = nvda_volume.rolling(window=20).mean()

    # ATR for SPY
    spy_atr = _compute_atr(spy["high"], spy["low"], spy_close, period=ATR_PERIOD)

    # Align indices
    common_dates = nvda_ret.index.intersection(spy_close.index)
    nvda_ret_align = nvda_ret.loc[common_dates]
    nvda_vol_align = nvda_volume.loc[common_dates]
    nvda_vol_ma_align = nvda_vol_ma20.loc[common_dates]
    spy_close_align = spy_close.loc[common_dates]
    spy_high_align = spy_high.loc[common_dates]
    spy_atr_align = spy_atr.loc[common_dates]

    spy_close_arr = spy_close_align.values.astype(float)
    spy_high_arr = spy_high_align.values.astype(float)
    spy_atr_arr = spy_atr_align.values.astype(float)
    nvda_ret_arr = nvda_ret_align.values.astype(float)
    nvda_vol_arr = nvda_vol_align.values.astype(float)
    nvda_vol_ma_arr = nvda_vol_ma_align.values.astype(float)

    signals: list[dict] = []

    # Need warmup for ATR + volume MA + return
    min_start = max(ATR_PERIOD, 22) + 2

    for i in range(min_start, len(common_dates)):
        if (np.isnan(nvda_ret_arr[i]) or np.isnan(spy_atr_arr[i]) or
                np.isnan(nvda_vol_ma_arr[i])):
            continue

        # Signal condition: NVDA drops > NVDA_DROP_PCT % with volume confirmation
        if nvda_ret_arr[i] < -NVDA_DROP_PCT:
            # Volume confirmation
            if nvda_vol_arr[i] < VOLUME_MULT * nvda_vol_ma_arr[i] and nvda_vol_ma_arr[i] > 0:
                continue

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

    from fetch_data import load_all
    print("Loading cached stock data...")
    stock_data = load_all()
    if not stock_data:
        print("ERROR: No cached data. Run with --fetch first.", file=sys.stderr)
        sys.exit(1)
    print(f"Loaded {len(stock_data)} tickers.")

    results = scan(stock_data)
    print(f"\nNVDA Breakdown signals found: {len(results)}")
    if results:
        print("\nFirst 3 signals:")
        for sig in results[:3]:
            for k, v in sig.items():
                print(f"  {k:25s}: {v}")
            print()