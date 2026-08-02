#!/usr/bin/env python3
"""
scanner_p_crosssectional.py — STR-P: Cross-Sectional Factor Ranking (Crypto)

First strategy built from factor evidence, not pattern matching.

Factor timing analysis showed:
  - MOM12_1 (12-month momentum) has Sharpe 1.32 in ranging crypto
  - LIQUID (dollar volume) has Sharpe 2.67 in ranging crypto
  - PRICEMOM has Sharpe 2.56 in ranging crypto

This scanner combines all three factors into a composite score, ranks all
cryptos cross-sectionally, and generates long signals for the top quintile
and short signals for the bottom quintile. This is the architecture our
per-ticker scanners cannot capture — the edge is in relative ranking,
not absolute thresholds.

Signal Rules:
  1. At each rebalance date, compute factor scores for all cryptos
  2. Rank cryptos by composite factor score (z-score weighted)
  3. Long the top quintile (highest composite score)
  4. Short the bottom quintile (lowest composite score)
  5. Hold until next rebalance (monthly = 21 bars)
  6. Exit: stop loss at 2x ATR, or time stop at next rebalance

This is a "batch" scanner — it takes the full crypto data dict, not a
single ticker DataFrame. Returns signals for all tickers at once.

Dependencies: pandas, numpy only.
"""

import numpy as np
import pandas as pd

STRATEGY_ID = "P_CROSSSECTIONAL_FACTOR"

# ── Parameters ───────────────────────────────────────────────────────────────
REBALANCE_FREQ = 21          # Rebalance every 21 bars (monthly)
QUINTILE = 5                 # Top/bottom quintile for long/short
ATR_PERIOD = 14              # ATR for stop placement
ATR_STOP_MULT = 1.5          # Stop = 1.5x ATR (optimized Phase 1B)
MAX_BARS_HELD = 21           # Hold until next rebalance (time stop = rebalance)
MIN_RR = 1.0                 # Minimum R:R (relaxed — factor ranking is the edge)

# Factor weights for composite score (sum to 1.0)
# Based on Sharpe ratios from factor timing analysis:
#   MOM12_1 Sharpe 1.32, LIQUID Sharpe 2.67, PRICEMOM Sharpe 2.56
FACTOR_WEIGHTS = {
    "MOM12_1": 0.33,    # 12-month momentum excluding recent month
    "LIQUID": 0.33,      # Liquidity (highest Sharpe in ranging crypto)
    "PRICEMOM": 0.34,   # Price relative to SMA200
}

# Factor lookback periods
MOM_LOOKBACK = 252          # 12 months
MOM_SKIP = 21                # Skip most recent month
LIQUID_LOOKBACK = 60         # 60-day average dollar volume
PRICEMOM_SMA = 200           # SMA period for PRICEMOM


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


def _compute_factor_scores(data: dict, date: pd.Timestamp) -> dict:
    """
    Compute factor scores for all tickers at a specific date.
    Returns {ticker: {factor_name: z_score, ...}} dict.
    """
    factor_values = {}

    for ticker, df in data.items():
        if len(df) < max(MOM_LOOKBACK + MOM_SKIP, PRICEMOM_SMA, LIQUID_LOOKBACK) + 5:
            continue

        # Find the date in the data (or closest prior)
        mask = df.index <= date
        if mask.sum() < max(MOM_LOOKBACK + MOM_SKIP, PRICEMOM_SMA, LIQUID_LOOKBACK):
            continue

        df_slice = df[mask]
        close = df_slice["close"]
        volume = df_slice["volume"]
        idx = len(df_slice) - 1

        # MOM12_1: 12-month return minus most recent month
        if idx >= MOM_LOOKBACK + MOM_SKIP:
            mom = close.iloc[idx - MOM_SKIP] / close.iloc[idx - MOM_LOOKBACK - MOM_SKIP] - 1
        else:
            continue

        # LIQUID: 60-day average dollar volume
        if idx >= LIQUID_LOOKBACK:
            dollar_vol = (close.iloc[idx-LIQUID_LOOKBACK:idx+1] * volume.iloc[idx-LIQUID_LOOKBACK:idx+1]).mean()
        else:
            continue

        # PRICEMOM: price relative to SMA200
        if idx >= PRICEMOM_SMA:
            sma = close.iloc[idx-PRICEMOM_SMA:idx+1].mean()
            pricemom = close.iloc[idx] / sma - 1
        else:
            continue

        factor_values[ticker] = {
            "MOM12_1": float(mom),
            "LIQUID": float(dollar_vol),
            "PRICEMOM": float(pricemom),
        }

    if len(factor_values) < QUINTILE:
        return {}

    # Convert to z-scores (cross-sectional standardization)
    for factor_name in FACTOR_WEIGHTS:
        values = [fv[factor_name] for fv in factor_values.values()]
        mean = np.mean(values)
        std = np.std(values)
        if std > 0:
            for ticker in factor_values:
                factor_values[ticker][f"{factor_name}_z"] = (
                    factor_values[ticker][factor_name] - mean
                ) / std
        else:
            for ticker in factor_values:
                factor_values[ticker][f"{factor_name}_z"] = 0.0

    # Compute composite score
    for ticker in factor_values:
        composite = 0.0
        for factor_name, weight in FACTOR_WEIGHTS.items():
            composite += weight * factor_values[ticker][f"{factor_name}_z"]
        factor_values[ticker]["composite"] = composite

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


def scan(data: dict, **kwargs) -> list:
    """
    Cross-sectional batch scanner. Takes the full crypto data dict,
    ranks all tickers by composite factor score, and generates signals.

    Parameters
    ----------
    data : dict
        {ticker: DataFrame} mapping for all crypto symbols
    **kwargs : ignored (interface compatibility)

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
    min_start = max(MOM_LOOKBACK + MOM_SKIP, PRICEMOM_SMA, LIQUID_LOOKBACK) + 5
    if len(all_dates) < min_start:
        return []

    # Find the earliest date that has enough history
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

        # Sort by composite score
        sorted_tickers = sorted(
            factor_scores.items(),
            key=lambda x: x[1]["composite"],
            reverse=True
        )

        n = len(sorted_tickers)
        quintile_size = n // QUINTILE
        if quintile_size < 1:
            continue

        # Long top quintile, short bottom quintile
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


def _create_signal(data: dict, ticker: str, date: pd.Timestamp,
                    direction: str, factor_scores: dict,
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
        bars_to_next = (df.index > date).sum()  # bars after entry date
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
        "factor_mom12_1": round(factor_scores.get("MOM12_1", 0), 4),
        "factor_liquid": round(factor_scores.get("LIQUID", 0), 2),
        "factor_pricemom": round(factor_scores.get("PRICEMOM", 0), 4),
        "composite_score": round(factor_scores.get("composite", 0), 4),
        "rebalance": True,
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent / "scripts" / "paper_trading"))
    from fetch_crypto_data import load_all as load_all_crypto

    print("Loading crypto data...")
    crypto = load_all_crypto()
    print(f"  {len(crypto)} symbols loaded")

    print("\nRunning STR-P cross-sectional factor ranking...")
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
    pf = sum(max(r, 0) for r in r_values) / max(abs(sum(min(r, 0) for r in r_values)), 0.01)

    print(f"\nSTR-P Phase 1A Results (Crypto):")
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
