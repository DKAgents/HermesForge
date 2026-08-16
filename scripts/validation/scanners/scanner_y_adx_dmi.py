#!/usr/bin/env python3
"""
scanner_y_adx_dmi.py
====================
HermesForge STR-Y: ADX/DMI Directional Movement Strategy

Compute ADX(14), +DI(14), -DI(14) using Wilder smoothing.

  LONG entry:  +DI crosses above -DI AND ADX > 25 (trending up).
  SHORT entry: -DI crosses above +DI AND ADX > 25 (trending down).
  Exit signal: opposite DI cross (handled via time-stop / mechanical exits here).

  Entry on cross bar close.
  Stop: 2 ATR(14).
  Target: 3R.
  Time stop: 20 bars.
  Long-only for stocks.

Dependencies: pandas, numpy
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

STRATEGY_ID = "STR-Y-adx-dmi"
STRATEGY_NAME = "ADX/DMI Directional Movement"
STRATEGY_VERSION = "1.0"
MAX_HOLD_BARS = 20
TARGET_RR = 3.0
STOP_ATR_MULT = 2.0
ADX_PERIOD = 14
ADX_THRESHOLD = 25.0


def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                  period: int = 14) -> pd.Series:
    """Average True Range (Wilder smoothing via EWM)."""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _compute_adx_dmi(high: pd.Series, low: pd.Series, close: pd.Series,
                     period: int = ADX_PERIOD) -> pd.DataFrame:
    """Compute ADX, +DI, -DI using Wilder smoothing.

    Returns DataFrame with columns: adx, plus_di, minus_di, atr.
    """
    prev_high = high.shift(1)
    prev_low = low.shift(1)
    prev_close = close.shift(1)

    up_move = high - prev_high
    down_move = prev_low - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm = pd.Series(plus_dm, index=high.index)
    minus_dm = pd.Series(minus_dm, index=high.index)

    atr = _compute_atr(high, low, close, period)

    # Wilder smoothing of +DM, -DM, TR (already smoothed in ATR)
    atr_smooth = atr  # already Wilder smoothed
    plus_dm_smooth = plus_dm.ewm(alpha=1.0 / period, adjust=False).mean()
    minus_dm_smooth = minus_dm.ewm(alpha=1.0 / period, adjust=False).mean()

    plus_di = 100 * plus_dm_smooth / atr_smooth.replace(0, np.nan)
    minus_di = 100 * minus_dm_smooth / atr_smooth.replace(0, np.nan)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1.0 / period, adjust=False).mean()

    return pd.DataFrame({
        "adx": adx,
        "plus_di": plus_di,
        "minus_di": minus_di,
        "atr": atr,
    }, index=high.index)


def scan(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    """Scan for ADX/DMI cross signals."""
    if len(df) < 50:
        return []

    df = df.copy()
    df.columns = df.columns.str.lower()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    indicators = _compute_adx_dmi(df["high"], df["low"], df["close"])
    adx = indicators["adx"].values
    plus_di = indicators["plus_di"].values
    minus_di = indicators["minus_di"].values
    atr_arr = indicators["atr"].values
    close_arr = df["close"].values.astype(float)

    signals = []
    min_start = ADX_PERIOD * 2 + 1

    for i in range(min_start, len(df)):
        if (np.isnan(adx[i]) or np.isnan(adx[i - 1]) or
                np.isnan(plus_di[i]) or np.isnan(minus_di[i]) or
                np.isnan(plus_di[i - 1]) or np.isnan(minus_di[i - 1]) or
                np.isnan(atr_arr[i])):
            continue

        # +DI crosses above -DI (bullish cross)
        plus_cross_up = plus_di[i - 1] <= minus_di[i - 1] and plus_di[i] > minus_di[i]
        # -DI crosses above +DI (bearish cross)
        minus_cross_up = minus_di[i - 1] <= plus_di[i - 1] and minus_di[i] > plus_di[i]

        trending = adx[i] > ADX_THRESHOLD

        entry_price = close_arr[i]

        # LONG
        if plus_cross_up and trending:
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
                "adx": round(adx[i], 2),
                "plus_di": round(plus_di[i], 2),
                "minus_di": round(minus_di[i], 2),
                "signal_type": "di_bullish_cross",
            })

        # SHORT
        if not long_only and minus_cross_up and trending:
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
                "adx": round(adx[i], 2),
                "plus_di": round(plus_di[i], 2),
                "minus_di": round(minus_di[i], 2),
                "signal_type": "di_bearish_cross",
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
    print(f"STR-Y ADX/DMI Phase 1A Backtest ({asset_type})")
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
    ap = argparse.ArgumentParser(description="STR-Y ADX/DMI Scanner")
    ap.add_argument("--backtest", action="store_true", help="Run Phase 1A backtest")
    ap.add_argument("--crypto", action="store_true", help="Backtest crypto instead of stocks")
    args = ap.parse_args()

    if args.backtest:
        if args.crypto:
            crypto_symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
            print("=== STR-Y Phase 1A Backtest (Crypto) ===\n")
            result = run_phase1a(crypto_symbols, "crypto")
        else:
            stock_symbols = [
                "SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL", "META",
                "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST",
            ]
            print("=== STR-Y Phase 1A Backtest (Stocks) ===\n")
            result = run_phase1a(stock_symbols, "stock")
            if len(result) > 0:
                out_path = Path(__file__).parent.parent / "results" / "STR-Y-stocks-phase1a.csv"
                result.to_csv(out_path, index=False)
                print(f"\nResults saved to {out_path}")
    else:
        print(__doc__)
