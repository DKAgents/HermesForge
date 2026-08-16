#!/usr/bin/env python3
"""
scanner_z_stochastic.py
=======================
HermesForge STR-Z: Stochastic Oscillator Strategy (v2.0 — structure-based)

Compute %K(14,3) [smoothed with 3-period SMA] and %D(3) [SMA of %K].

  LONG:  %K crosses above %D AND %K < 20 (oversold).
  SHORT: %K crosses below %D AND %K > 80 (overbought).

v2.0 changes (US-115): the stochastic cross remains the *signal trigger only*.
Entry, stop, and target are now derived from market structure via the shared
`market_structure.compute_structure_trade` orchestrator:
  * Entry  = pullback to nearest confirmed support after the cross (limit order,
             up to 5 bars wait; market fallback at signal close if no touch).
  * Stop   = nearest confirmed swing low/high below/above entry, ATR-buffered,
             capped at 2 ATR, floored at 0.5 ATR.
  * Target = nearest confirmed overhead/below resistance offering R >= 1.5
             (ATR fallback if no structural target qualifies; skip if none).
R-multiple on target exits is computed from actual prices (no longer fixed 3R).
A 20-bar per-ticker cooldown suppresses overlapping signals.

v1.x behaviour: entry=close[i], stop=1.5 ATR, target=3R fixed.

Dependencies: pandas, numpy
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from market_structure import compute_structure_trade

STRATEGY_ID = "STR-Z-stochastic"
STRATEGY_NAME = "Stochastic Oscillator"
STRATEGY_VERSION = "2.0"
MAX_HOLD_BARS = 15
COOLDOWN_BARS = 20
K_PERIOD = 14
K_SMOOTH = 3
D_PERIOD = 3


def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                  period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _compute_stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                        k_period: int = K_PERIOD, k_smooth: int = K_SMOOTH,
                        d_period: int = D_PERIOD) -> pd.DataFrame:
    """Compute Stochastic %K (fast %K smoothed by k_smooth SMA) and %D (SMA of %K)."""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    fast_k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    # Slow %K = SMA of fast %K
    k = fast_k.rolling(window=k_smooth).mean()
    # %D = SMA of slow %K
    d = k.rolling(window=d_period).mean()
    return pd.DataFrame({"k": k, "d": d}, index=close.index)


def scan(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    if len(df) < 50:
        return []

    df = df.copy()
    df.columns = df.columns.str.lower()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    stoch = _compute_stochastic(df["high"], df["low"], df["close"])
    atr = _compute_atr(df["high"], df["low"], df["close"])
    k_arr = stoch["k"].values
    d_arr = stoch["d"].values

    signals = []
    min_start = K_PERIOD + K_SMOOTH + D_PERIOD + 1
    cooldown_until = 0

    for i in range(min_start, len(df)):
        if (np.isnan(k_arr[i]) or np.isnan(k_arr[i - 1]) or
                np.isnan(d_arr[i]) or np.isnan(d_arr[i - 1])):
            continue

        # %K crosses above %D (bullish)
        k_cross_up = k_arr[i - 1] <= d_arr[i - 1] and k_arr[i] > d_arr[i]
        # %K crosses below %D (bearish)
        k_cross_down = k_arr[i - 1] >= d_arr[i - 1] and k_arr[i] < d_arr[i]

        # LONG: %K crosses above %D AND %K < 20
        if k_cross_up and k_arr[i] < 20:
            if i < cooldown_until:
                continue
            trade = compute_structure_trade(
                df, signal_idx=i, direction="long",
                max_wait_bars=5, min_rr=1.5, max_atr=2.0, atr=atr,
                entry_fallback="signal",
            )
            if trade is None:
                continue
            signals.append({
                "date": df.index[i],
                "entry_date": df.index[trade["entry_idx"]],
                "entry_idx": trade["entry_idx"],
                "ticker": ticker,
                "strategy_id": STRATEGY_ID,
                "strategy_name": STRATEGY_NAME,
                "strategy_version": STRATEGY_VERSION,
                "direction": "long",
                "entry_price": round(trade["entry_price"], 4),
                "stop_price": round(trade["stop_price"], 4),
                "target_price": round(trade["target_price"], 4),
                "risk": round(trade["risk"], 4),
                "rr": round(trade["rr"], 3),
                "entry_type": trade["entry_type"],
                "pct_k": round(k_arr[i], 2),
                "pct_d": round(d_arr[i], 2),
                "signal_type": "stoch_bullish_cross_oversold",
            })
            cooldown_until = i + COOLDOWN_BARS

        # SHORT: %K crosses below %D AND %K > 80
        if not long_only and k_cross_down and k_arr[i] > 80:
            if i < cooldown_until:
                continue
            trade = compute_structure_trade(
                df, signal_idx=i, direction="short",
                max_wait_bars=5, min_rr=1.5, max_atr=2.0, atr=atr,
                entry_fallback="signal",
            )
            if trade is None:
                continue
            signals.append({
                "date": df.index[i],
                "entry_date": df.index[trade["entry_idx"]],
                "entry_idx": trade["entry_idx"],
                "ticker": ticker,
                "strategy_id": STRATEGY_ID,
                "strategy_name": STRATEGY_NAME,
                "strategy_version": STRATEGY_VERSION,
                "direction": "short",
                "entry_price": round(trade["entry_price"], 4),
                "stop_price": round(trade["stop_price"], 4),
                "target_price": round(trade["target_price"], 4),
                "risk": round(trade["risk"], 4),
                "rr": round(trade["rr"], 3),
                "entry_type": trade["entry_type"],
                "pct_k": round(k_arr[i], 2),
                "pct_d": round(d_arr[i], 2),
                "signal_type": "stoch_bearish_cross_overbought",
            })
            cooldown_until = i + COOLDOWN_BARS

    return signals


def _walk_forward_exit(df: pd.DataFrame, entry_idx: int, direction: str,
                       entry_price: float, stop_price: float, target_price: float,
                       max_bars: int = MAX_HOLD_BARS) -> dict:
    n = len(df)
    risk = (entry_price - stop_price) if direction == "long" else (stop_price - entry_price)
    for i in range(entry_idx + 1, min(entry_idx + max_bars + 1, n)):
        bar = df.iloc[i]
        if direction == "long":
            if bar["low"] <= stop_price:
                return {"exit_type": "stop", "exit_price": stop_price,
                        "bars_held": i - entry_idx, "r_multiple": -1.0}
            if bar["high"] >= target_price:
                gain = target_price - entry_price
                r_mult = round(gain / risk, 3) if risk > 0 else 0.0
                return {"exit_type": "target", "exit_price": target_price,
                        "bars_held": i - entry_idx, "r_multiple": r_mult}
        else:
            if bar["high"] >= stop_price:
                return {"exit_type": "stop", "exit_price": stop_price,
                        "bars_held": i - entry_idx, "r_multiple": -1.0}
            if bar["low"] <= target_price:
                gain = entry_price - target_price
                r_mult = round(gain / risk, 3) if risk > 0 else 0.0
                return {"exit_type": "target", "exit_price": target_price,
                        "bars_held": i - entry_idx, "r_multiple": r_mult}

    exit_idx = min(entry_idx + max_bars, n - 1)
    exit_price = df.iloc[exit_idx]["close"]
    if risk <= 0:
        r = 0.0
    else:
        r = ((exit_price - entry_price) / risk) if direction == "long" \
            else ((entry_price - exit_price) / risk)
    return {"exit_type": "time", "exit_price": round(exit_price, 4),
            "bars_held": max_bars, "r_multiple": round(r, 3)}


def run_backtest(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    signals = scan(df, ticker, long_only=long_only)
    if not signals:
        return []

    df = df.copy()
    df.columns = df.columns.str.lower()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    trades = []
    for sig in signals:
        entry_idx = sig.get("entry_idx")
        if entry_idx is None:
            target_date = pd.Timestamp(sig["date"])
            try:
                entry_idx = df.index.get_loc(target_date)
            except (KeyError, ValueError, TypeError):
                mask = df.index == target_date
                if not mask.any():
                    continue
                entry_idx = df.index.get_loc(df.index[mask][0])

        if isinstance(entry_idx, slice):
            entry_idx = entry_idx.start
        if isinstance(entry_idx, (list, np.ndarray)):
            entry_idx = int(entry_idx[0])
        if entry_idx + 1 >= len(df):
            continue

        exit_result = _walk_forward_exit(
            df, int(entry_idx), sig["direction"],
            sig["entry_price"], sig["stop_price"], sig["target_price"],
        )
        trades.append({
            "symbol": ticker,
            "strategy": STRATEGY_ID,
            "direction": sig["direction"],
            "date": sig["date"],
            "entry_price": round(sig["entry_price"], 4),
            "stop_price": round(sig["stop_price"], 4),
            "target_price": round(sig["target_price"], 4),
            "exit_type": exit_result["exit_type"],
            "exit_price": round(exit_result["exit_price"], 4),
            "bars_held": exit_result["bars_held"],
            "r_multiple": exit_result["r_multiple"],
            "signal_type": sig["signal_type"],
        })

    return trades


def run_phase1a(symbols: list, asset_type: str = "stock") -> pd.DataFrame:
    DATA_DIR = Path.home() / ".hermes" / "market_data"
    all_trades = []

    for sym in symbols:
        print(f"  Scanning {sym}...", flush=True)
        cache_path = DATA_DIR / f"{sym}.parquet"
        if not cache_path.exists():
            print(f"    No cached data for {sym}")
            continue
        df = pd.read_parquet(cache_path)
        if "Date" in df.columns:
            df = df.set_index("Date")
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df.columns = df.columns.str.lower()

        if len(df) < 50:
            print(f"    Only {len(df)} bars — skipping")
            continue

        long_only = (asset_type == "stock")
        trades = run_backtest(df, sym, long_only=long_only)
        all_trades.extend(trades)
        print(f"    {len(trades)} signals found")

    if not all_trades:
        print("\nNo signals found across all symbols!")
        return pd.DataFrame()

    df = pd.DataFrame(all_trades)
    print(f"\n{'='*60}")
    print(f"STR-Z Stochastic Oscillator Phase 1A Backtest ({asset_type})")
    print(f"{'='*60}")
    _print_summary(df)
    return df


def _print_summary(df: pd.DataFrame) -> None:
    print(f"Total signals: {len(df)}")
    print(f"Win rate: {(df['r_multiple'] > 0).mean() * 100:.1f}%")
    print(f"Average R: {df['r_multiple'].mean():.3f}")
    print(f"Median R: {df['r_multiple'].median():.3f}")
    print(f"Sum R: {df['r_multiple'].sum():.3f}")
    print(f"Max win: {df['r_multiple'].max():.3f}R")
    print(f"Max loss: {df['r_multiple'].min():.3f}R")
    print(f"Avg bars held: {df['bars_held'].mean():.1f}")

    print(f"\nBy direction:")
    for d in ["long", "short"]:
        s = df[df["direction"] == d]
        if len(s) > 0:
            print(f"  {d}: {len(s)} trades, WR={((s['r_multiple'] > 0).mean() * 100):.1f}%, "
                  f"avg R={s['r_multiple'].mean():.3f}")

    print(f"\nBy exit type:")
    for et in ["target", "stop", "time"]:
        s = df[df["exit_type"] == et]
        if len(s) > 0:
            print(f"  {et}: {len(s)} trades, avg R={s['r_multiple'].mean():.3f}")

    pos_r = df[df["r_multiple"] > 0]["r_multiple"].sum()
    neg_r = abs(df[df["r_multiple"] < 0]["r_multiple"].sum())
    pf = pos_r / neg_r if neg_r > 0 else float('inf')
    print(f"\nProfit factor: {pf:.2f}")

    print(f"\nBy symbol:")
    for sym in sorted(df["symbol"].unique()):
        s = df[df["symbol"] == sym]
        print(f"  {sym}: {len(s)} trades, WR={((s['r_multiple'] > 0).mean() * 100):.1f}%, "
              f"avg R={s['r_multiple'].mean():.3f}, sum R={s['r_multiple'].sum():.2f}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="STR-Z Stochastic Scanner")
    ap.add_argument("--backtest", action="store_true", help="Run Phase 1A backtest")
    ap.add_argument("--crypto", action="store_true", help="Backtest crypto instead of stocks")
    args = ap.parse_args()

    if args.backtest:
        if args.crypto:
            crypto_symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
            print("=== STR-Z Phase 1A Backtest (Crypto) ===\n")
            result = run_phase1a(crypto_symbols, "crypto")
        else:
            stock_symbols = [
                "SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL", "META",
                "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST",
            ]
            print("=== STR-Z Phase 1A Backtest (Stocks) ===\n")
            result = run_phase1a(stock_symbols, "stock")
            if len(result) > 0:
                out_path = Path(__file__).parent.parent / "results" / "STR-Z-stocks-phase1a.csv"
                result.to_csv(out_path, index=False)
                print(f"\nResults saved to {out_path}")
    else:
        print(__doc__)
