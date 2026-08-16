#!/usr/bin/env python3
"""
scanner_ac_cci.py
=================
HermesForge STR-AC: Commodity Channel Index (CCI) Strategy

CCI(20) = (Typical Price - SMA(20)) / (0.015 * Mean Deviation)
  where Typical Price = (high + low + close) / 3
  and Mean Deviation = mean of |Typical Price - SMA(20)| over the window.

  LONG:  CCI crosses above -100 from below (oversold exit).
  SHORT: CCI crosses below +100 from above (overbought exit).

  Entry on cross bar close.
  Stop: 1.5 ATR(14).
  Target: 3R.
  Time stop: 15 bars.
  Long-only for stocks.

Dependencies: pandas, numpy
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

STRATEGY_ID = "STR-AC-cci"
STRATEGY_NAME = "Commodity Channel Index"
STRATEGY_VERSION = "1.0"
MAX_HOLD_BARS = 15
TARGET_RR = 3.0
STOP_ATR_MULT = 1.5
CCI_PERIOD = 20
OVERSOLD = -100.0
OVERBOUGHT = 100.0


def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                  period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _compute_cci(high: pd.Series, low: pd.Series, close: pd.Series,
                 period: int = CCI_PERIOD) -> pd.Series:
    typical = (high + low + close) / 3.0
    sma = typical.rolling(window=period).mean()
    # Mean deviation: mean of |typical - sma| over the window (per-bar rolling)
    # Vectorized: for each bar, average |typical[i-k] - sma[i]| for k in 0..period-1
    # Use a rolling apply on the typical series with the sma value at the END of window.
    mean_dev = typical.rolling(window=period).apply(
        lambda x: np.mean(np.abs(x - x.mean())), raw=True
    )
    cci = (typical - sma) / (0.015 * mean_dev.replace(0, np.nan))
    return cci


def scan(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    if len(df) < 50:
        return []

    df = df.copy()
    df.columns = df.columns.str.lower()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    cci = _compute_cci(df["high"], df["low"], df["close"])
    atr = _compute_atr(df["high"], df["low"], df["close"])
    cci_arr = cci.values
    atr_arr = atr.values
    close_arr = df["close"].values.astype(float)

    signals = []
    min_start = CCI_PERIOD + 1

    for i in range(min_start, len(df)):
        if (np.isnan(cci_arr[i]) or np.isnan(cci_arr[i - 1]) or
                np.isnan(atr_arr[i])):
            continue

        # CCI crosses above -100 (oversold exit -> long)
        cci_cross_up = cci_arr[i - 1] < OVERSOLD and cci_arr[i] >= OVERSOLD
        # CCI crosses below +100 (overbought exit -> short)
        cci_cross_down = cci_arr[i - 1] > OVERBOUGHT and cci_arr[i] <= OVERBOUGHT

        entry_price = close_arr[i]

        if cci_cross_up:
            stop_price = entry_price - STOP_ATR_MULT * atr_arr[i]
            risk = entry_price - stop_price
            if risk <= 0:
                continue
            target_price = entry_price + risk * TARGET_RR
            ts = df.index[i]
            signals.append({
                "date": ts,
                "ticker": ticker,
                "strategy_id": STRATEGY_ID,
                "strategy_name": STRATEGY_NAME,
                "strategy_version": STRATEGY_VERSION,
                "direction": "long",
                "entry_price": round(entry_price, 4),
                "stop_price": round(stop_price, 4),
                "target_price": round(target_price, 4),
                "cci": round(cci_arr[i], 2),
                "signal_type": "cci_oversold_exit_long",
            })

        if not long_only and cci_cross_down:
            stop_price = entry_price + STOP_ATR_MULT * atr_arr[i]
            risk = stop_price - entry_price
            if risk <= 0:
                continue
            target_price = entry_price - risk * TARGET_RR
            ts = df.index[i]
            signals.append({
                "date": ts,
                "ticker": ticker,
                "strategy_id": STRATEGY_ID,
                "strategy_name": STRATEGY_NAME,
                "strategy_version": STRATEGY_VERSION,
                "direction": "short",
                "entry_price": round(entry_price, 4),
                "stop_price": round(stop_price, 4),
                "target_price": round(target_price, 4),
                "cci": round(cci_arr[i], 2),
                "signal_type": "cci_overbought_exit_short",
            })

    return signals


def _walk_forward_exit(df: pd.DataFrame, entry_idx: int, direction: str,
                       entry_price: float, stop_price: float, target_price: float,
                       max_bars: int = MAX_HOLD_BARS) -> dict:
    n = len(df)
    for i in range(entry_idx + 1, min(entry_idx + max_bars + 1, n)):
        bar = df.iloc[i]
        if direction == "long":
            if bar["low"] <= stop_price:
                return {"exit_type": "stop", "exit_price": stop_price,
                        "bars_held": i - entry_idx, "r_multiple": -1.0}
            if bar["high"] >= target_price:
                return {"exit_type": "target", "exit_price": target_price,
                        "bars_held": i - entry_idx, "r_multiple": TARGET_RR}
        else:
            if bar["high"] >= stop_price:
                return {"exit_type": "stop", "exit_price": stop_price,
                        "bars_held": i - entry_idx, "r_multiple": -1.0}
            if bar["low"] <= target_price:
                return {"exit_type": "target", "exit_price": target_price,
                        "bars_held": i - entry_idx, "r_multiple": TARGET_RR}

    exit_idx = min(entry_idx + max_bars, n - 1)
    exit_price = df.iloc[exit_idx]["close"]
    risk = (entry_price - stop_price) if direction == "long" else (stop_price - entry_price)
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
    print(f"STR-AC CCI Phase 1A Backtest ({asset_type})")
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
    ap = argparse.ArgumentParser(description="STR-AC CCI Scanner")
    ap.add_argument("--backtest", action="store_true", help="Run Phase 1A backtest")
    ap.add_argument("--crypto", action="store_true", help="Backtest crypto instead of stocks")
    args = ap.parse_args()

    if args.backtest:
        if args.crypto:
            crypto_symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
            print("=== STR-AC Phase 1A Backtest (Crypto) ===\n")
            result = run_phase1a(crypto_symbols, "crypto")
        else:
            stock_symbols = [
                "SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL", "META",
                "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST",
            ]
            print("=== STR-AC Phase 1A Backtest (Stocks) ===\n")
            result = run_phase1a(stock_symbols, "stock")
            if len(result) > 0:
                out_path = Path(__file__).parent.parent / "results" / "STR-AC-stocks-phase1a.csv"
                result.to_csv(out_path, index=False)
                print(f"\nResults saved to {out_path}")
    else:
        print(__doc__)
