#!/usr/bin/env python3
"""
scanner_add_factor.py — STR-ADD-FACTOR: Anomaly-Driven Demand Cross-Sectional Ranking

Based on the academic paper "Anomaly-Driven Demand" (Posselt & Kjær, 2026, SSRN 6342599).

The ADD measure counts how many anomaly portfolios a stock enters the long leg of,
minus those it enters the short leg of. Stocks with high ADD face coordinated buying
pressure from mechanical factor rebalancing.

This is a batch scanner (scan(data_dict)) that:
1. At each rebalance date (weekly = every 5 days), computes a proxy ADD score for
   every stock using available price/volume data
2. Proxies for anomaly membership:
   - VALUE proxy: price / 200-day SMA (below median = cheap = long leg)
   - MOMENTUM: 12-month return minus 1-month (above median = long leg)
   - LOW VOLATILITY: 60-day rolling vol (below median = long leg)
   - RECENT STRENGTH: 5-day return (above median = long leg)
   - VOLUME ANOMALY: volume / 20-day avg volume > 1.5 (spike = long leg)
3. Long the top ADD quintile, short the bottom ADD quintile
4. Hold until next rebalance with ATR-based stop

Dependencies: pandas, numpy only.
"""

import numpy as np
import pandas as pd

STRATEGY_ID = "STR-ADD-FACTOR"
STRATEGY_NAME = "Anomaly-Driven Demand Factor"
STRATEGY_VERSION = "1.0"

# ── Parameters ───────────────────────────────────────────────────────────────
REBALANCE_FREQ = 5           # Rebalance every 5 bars (weekly)
QUINTILE = 5                  # Top/bottom quintile for long/short
ATR_PERIOD = 14               # ATR for stop placement
ATR_STOP_MULT = 2.0           # Stop = 2.0x ATR
MAX_BARS_HELD = 5             # Hold until next rebalance (weekly)

# Anomaly proxy parameters
SMA_PERIOD = 200              # Long-term SMA for value proxy
MOM_LOOKBACK = 252            # 12 months for momentum
MOM_SKIP = 21                 # Skip most recent month
LOWVOL_PERIOD = 60            # 60-day vol lookback
SHORT_STRENGTH_PERIOD = 5     # 5-day return for recent strength
VOL_SURGE_MULT = 1.5          # Volume spike threshold
VOL_AVG_PERIOD = 20           # Volume average period


def _compute_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    """Average True Range (Wilder's EMA)."""
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _compute_add_scores(data: dict, date: pd.Timestamp) -> dict:
    """
    Compute proxy ADD scores for all tickers at a specific date.
    Returns {ticker: {anomaly_long_count, anomaly_short_count, add_score, ...}}
    """
    # Raw factor values
    raw = {}

    for ticker, df in data.items():
        if len(df) < max(MOM_LOOKBACK + MOM_SKIP, SMA_PERIOD, LOWVOL_PERIOD, VOL_AVG_PERIOD) + 10:
            continue

        mask = df.index <= date
        if mask.sum() < max(MOM_LOOKBACK + MOM_SKIP, SMA_PERIOD, LOWVOL_PERIOD, VOL_AVG_PERIOD):
            continue

        df_slice = df[mask]
        close = df_slice["close"]
        volume = df_slice["volume"]
        idx = len(df_slice) - 1

        if idx < 5:
            continue

        # 1. VALUE proxy: price / 200-day SMA (low = undervalued)
        if idx >= SMA_PERIOD:
            sma200 = close.iloc[idx - SMA_PERIOD:idx + 1].mean()
            value_ratio = close.iloc[idx] / sma200 if sma200 > 0 else 1.0
        else:
            continue

        # 2. MOMENTUM: 12-month return minus 1-month
        if idx >= MOM_LOOKBACK + MOM_SKIP:
            momentum = close.iloc[idx - MOM_SKIP] / close.iloc[idx - MOM_LOOKBACK - MOM_SKIP] - 1
        else:
            continue

        # 3. LOW VOLATILITY: 60-day daily return volatility
        if idx >= LOWVOL_PERIOD:
            returns = close.iloc[idx - LOWVOL_PERIOD:idx + 1].pct_change().dropna()
            vol_60d = returns.std()
        else:
            continue

        # 4. RECENT STRENGTH: 5-day return
        if idx >= SHORT_STRENGTH_PERIOD:
            strength_5d = close.iloc[idx] / close.iloc[idx - SHORT_STRENGTH_PERIOD] - 1
        else:
            continue

        # 5. VOLUME ANOMALY: volume spike
        if idx >= VOL_AVG_PERIOD:
            avg_vol = volume.iloc[idx - VOL_AVG_PERIOD:idx + 1].mean()
            vol_ratio = volume.iloc[idx] / avg_vol if avg_vol > 0 else 1.0
        else:
            continue

        raw[ticker] = {
            "value_ratio": float(value_ratio),
            "momentum": float(momentum),
            "vol_60d": float(vol_60d),
            "strength_5d": float(strength_5d),
            "vol_ratio": float(vol_ratio),
        }

    if len(raw) < QUINTILE:
        return {}

    # Cross-sectional median for each factor (anomaly membership = above/below median)
    factor_keys = ["value_ratio", "momentum", "vol_60d", "strength_5d", "vol_ratio"]
    medians = {}
    for fk in factor_keys:
        vals = [raw[t][fk] for t in raw]
        medians[fk] = np.median(vals)

    # Compute ADD score = long-leg count - short-leg count
    # Long leg conditions (stock enters anomaly long portfolio):
    #   VALUE: value_ratio < median (cheap = long leg)
    #   MOMENTUM: momentum > median (winners = long leg)
    #   LOW VOL: vol_60d < median (low vol = long leg)
    #   STRENGTH: strength_5d > median (recent strength = long leg)
    #   VOLUME: vol_ratio > 1.5 (volume spike = long leg)
    #
    # Short leg conditions:
    #   VALUE: value_ratio > median (expensive = short leg)
    #   MOMENTUM: momentum < median (losers = short leg)
    #   LOW VOL: vol_60d > median (high vol = short leg)
    #   STRENGTH: strength_5d < median (recent weakness = short leg)
    #   VOLUME: vol_ratio < 0.5 (volume drought = short leg)

    scores = {}
    for ticker in raw:
        v = raw[ticker]
        long_count = 0
        short_count = 0

        # Value: cheap = long, expensive = short
        if v["value_ratio"] < medians["value_ratio"]:
            long_count += 1
        else:
            short_count += 1

        # Momentum: winners = long, losers = short
        if v["momentum"] > medians["momentum"]:
            long_count += 1
        else:
            short_count += 1

        # Low volatility: low vol = long, high vol = short
        if v["vol_60d"] < medians["vol_60d"]:
            long_count += 1
        else:
            short_count += 1

        # Recent strength: strong = long, weak = short
        if v["strength_5d"] > medians["strength_5d"]:
            long_count += 1
        else:
            short_count += 1

        # Volume anomaly: spike = long, drought = short
        if v["vol_ratio"] > VOL_SURGE_MULT:
            long_count += 1
        if v["vol_ratio"] < 0.5:
            short_count += 1

        scores[ticker] = {
            "add_score": long_count - short_count,
            "long_count": long_count,
            "short_count": short_count,
            "max_possible": 5,
        }

    return scores


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
                   direction: str, add_info: dict) -> dict:
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
    if atr_val <= 0:
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

    # Simulate exit using full data
    exit_price, exit_reason, bars_held = _simulate_exit(
        df, entry_idx, direction, entry_price, stop_price, MAX_BARS_HELD
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
        "add_score": add_info.get("add_score", 0),
        "long_count": add_info.get("long_count", 0),
        "short_count": add_info.get("short_count", 0),
        "rebalance": True,
    }


def scan(data: dict, **kwargs) -> list:
    """
    Cross-sectional ADD batch scanner. Takes the full stock data dict,
    ranks all tickers by ADD proxy score, and generates signals.

    Parameters
    ----------
    data : dict
        {ticker: DataFrame} mapping for all stock symbols
    **kwargs : ignored (interface compatibility)

    Returns
    -------
    list of dict, one per signal (long top quintile, short bottom quintile)
    """
    if not data or len(data) < QUINTILE:
        return []

    # Get all unique dates across all tickers
    all_dates = set()
    for df in data.values():
        all_dates.update(df.index)
    all_dates = sorted(all_dates)

    min_bars = max(MOM_LOOKBACK + MOM_SKIP, SMA_PERIOD, LOWVOL_PERIOD, VOL_AVG_PERIOD) + 10
    if len(all_dates) < min_bars:
        return []

    # Find a reasonable start date
    first_df = list(data.values())[0]
    start_date = first_df.index[min_bars] if len(first_df) > min_bars else all_dates[min_bars]
    all_dates = [d for d in all_dates if d >= start_date]

    # Rebalance dates (weekly = every 5 trading days)
    rebalance_dates = all_dates[::REBALANCE_FREQ]

    signals = []

    for rebalance_idx, rebalance_date in enumerate(rebalance_dates):
        # Compute ADD scores at this date
        add_scores = _compute_add_scores(data, rebalance_date)
        if len(add_scores) < QUINTILE:
            continue

        # Sort by ADD score descending
        sorted_tickers = sorted(
            add_scores.items(),
            key=lambda x: x[1]["add_score"],
            reverse=True
        )

        n = len(sorted_tickers)
        quintile_size = n // QUINTILE
        if quintile_size < 1:
            continue

        # Long top quintile (highest ADD), short bottom quintile (lowest ADD)
        long_tickers = [t for t, _ in sorted_tickers[:quintile_size]]
        short_tickers = [t for t, _ in sorted_tickers[-quintile_size:]]

        for ticker in long_tickers:
            sig = _create_signal(
                data, ticker, rebalance_date, "long",
                add_scores[ticker]
            )
            if sig:
                signals.append(sig)

        for ticker in short_tickers:
            sig = _create_signal(
                data, ticker, rebalance_date, "short",
                add_scores[ticker]
            )
            if sig:
                signals.append(sig)

    return signals


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
    from fetch_data import load_all

    print("Loading stock data...")
    stocks = load_all()
    print(f"  {len(stocks)} symbols loaded")

    print("\nRunning STR-ADD-FACTOR cross-sectional ranking...")
    signals = scan(stocks)

    if not signals:
        print("No signals generated.")
        sys.exit(0)

    r_values = [s["r_multiple"] for s in signals]
    long_sigs = [s for s in signals if s["direction"] == "long"]
    short_sigs = [s for s in signals if s["direction"] == "short"]
    wins = [s for s in signals if s["r_multiple"] > 0]
    avg_r = float(np.mean(r_values))
    win_rate = len(wins) / len(signals)

    print(f"\nSTR-ADD-FACTOR Phase 1A Results (Stocks):")
    print(f"  Signals: {len(signals)} ({len(long_sigs)} long, {len(short_sigs)} short)")
    print(f"  Avg R: {avg_r:+.4f}")
    print(f"  Win rate: {win_rate:.1%}")
    print(f"  Median R: {float(np.median(r_values)):+.4f}")

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
        print(f"    {yr}: {len(yr_r):3d} sigs, avg R = {float(np.mean(yr_r)):+.4f}")

    # Long vs short
    long_r = [s["r_multiple"] for s in long_sigs]
    short_r = [s["r_multiple"] for s in short_sigs]
    print(f"\n  Long only:  {len(long_r):3d} sigs, avg R = {float(np.mean(long_r)):+.4f}")
    print(f"  Short only: {len(short_r):3d} sigs, avg R = {float(np.mean(short_r)):+.4f}")