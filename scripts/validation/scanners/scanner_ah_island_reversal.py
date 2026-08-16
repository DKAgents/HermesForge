#!/usr/bin/env python3
"""
scanner_ah_island_reversal.py
=============================
HermesForge STR-AH: Island Reversal

An island reversal is an isolated segment of price action bounded by gaps on
both sides — a gap in one direction, 1-5 bars of trading, then a gap in the
opposite direction. The "island" is the orphaned price segment.

Signal Rules:
  LONG  (bullish island reversal): gap down followed by gap up
        (price gaps down, trades for 1-5 bars, then gaps back up above the
         pre-gap-down bar's high)
  SHORT (bearish island reversal): gap up followed by gap down
        (price gaps up, trades for 1-5 bars, then gaps back down below the
         pre-gap-up bar's low)

Entry on the second gap bar close.
Stop: island extreme (lowest low for long, highest high for short).
Target: 3R.
Time stop: 15 bars.

Long-only for stocks.

Dependencies: pandas, numpy
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

STRATEGY_ID = "STR-AH-island"
STRATEGY_NAME = "Island Reversal"
STRATEGY_VERSION = "1.0"
MAX_HOLD_BARS = 15
TARGET_RR = 3.0
MIN_ISLAND_BARS = 1
MAX_ISLAND_BARS = 5


def _gaps(df: pd.DataFrame) -> pd.DataFrame:
    """Compute gap up/down flags and gap sizes vs prior bar."""
    prev_high = df["high"].shift(1)
    prev_low = df["low"].shift(1)
    gap_up = df["low"] > prev_high        # today's low above prior high
    gap_down = df["high"] < prev_low      # today's high below prior low
    out = df.copy()
    out["gap_up"] = gap_up.fillna(False)
    out["gap_down"] = gap_down.fillna(False)
    out["prev_high"] = prev_high
    out["prev_low"] = prev_low
    return out


def scan(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    if len(df) < 10:
        return []
    res = _gaps(df)
    n = len(res)
    signals = []

    for i in range(2, n):
        # We need a "first gap" earlier and a "second gap" at bar i.
        # Look back 1..5 bars for the first gap of opposite type.
        if not (res["gap_up"].iloc[i] or res["gap_down"].iloc[i]):
            continue

        # BULLISH island: first gap down, then gap up at bar i
        if res["gap_up"].iloc[i]:
            for k in range(MIN_ISLAND_BARS, MAX_ISLAND_BARS + 1):
                j = i - k - 1  # bar before the island segment (pre-gap bar)
                if j < 1:
                    break
                # The first gap (gap down) should occur at bar j+1
                if not res["gap_down"].iloc[j + 1]:
                    continue
                # Island segment is bars j+1 .. i-1, second gap at i
                island = res.iloc[j + 1:i]
                island_low = island["low"].min()
                # The pre-gap-down bar's low is res.prev_low.iloc[j+1] but we want
                # the island extreme (lowest low within the island) as the stop.
                # The gap up at i must clear the pre-gap-down bar's high.
                pre_bar_high = res["high"].iloc[j]
                if res["low"].iloc[i] > pre_bar_high:
                    entry_price = res["close"].iloc[i]
                    stop_price = island_low
                    risk = entry_price - stop_price
                    if risk <= 0:
                        continue
                    target_price = entry_price + risk * TARGET_RR
                    signals.append({
                        "date": res.index[i],
                        "ticker": ticker,
                        "strategy_id": STRATEGY_ID,
                        "strategy_name": STRATEGY_NAME,
                        "strategy_version": STRATEGY_VERSION,
                        "direction": "long",
                        "entry_price": entry_price,
                        "stop_price": stop_price,
                        "target_price": target_price,
                        "island_low": island_low,
                        "island_high": island["high"].max(),
                        "island_bars": k,
                        "signal_type": "island_bullish_long",
                    })
                    break  # only one signal per second-gap bar

        # BEARISH island: first gap up, then gap down at bar i
        if not long_only and res["gap_down"].iloc[i]:
            for k in range(MIN_ISLAND_BARS, MAX_ISLAND_BARS + 1):
                j = i - k - 1
                if j < 1:
                    break
                if not res["gap_up"].iloc[j + 1]:
                    continue
                island = res.iloc[j + 1:i]
                island_high = island["high"].max()
                pre_bar_low = res["low"].iloc[j]
                if res["high"].iloc[i] < pre_bar_low:
                    entry_price = res["close"].iloc[i]
                    stop_price = island_high
                    risk = stop_price - entry_price
                    if risk <= 0:
                        continue
                    target_price = entry_price - risk * TARGET_RR
                    signals.append({
                        "date": res.index[i],
                        "ticker": ticker,
                        "strategy_id": STRATEGY_ID,
                        "strategy_name": STRATEGY_NAME,
                        "strategy_version": STRATEGY_VERSION,
                        "direction": "short",
                        "entry_price": entry_price,
                        "stop_price": stop_price,
                        "target_price": target_price,
                        "island_low": island["low"].min(),
                        "island_high": island_high,
                        "island_bars": k,
                        "signal_type": "island_bearish_short",
                    })
                    break

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
    r = ((exit_price - entry_price) / risk) if direction == "long" else ((entry_price - exit_price) / risk)
    if risk <= 0:
        r = 0.0
    return {"exit_type": "time", "exit_price": exit_price,
            "bars_held": exit_idx - entry_idx, "r_multiple": round(r, 3)}


def run_backtest(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    signals = scan(df, ticker, long_only=long_only)
    if not signals:
        return []
    trades = []
    for sig in signals:
        try:
            target_date = pd.Timestamp(sig["date"])
            entry_idx = df.index.get_loc(df.index[df.index == target_date][0])
        except (KeyError, ValueError, IndexError, TypeError):
            continue
        if entry_idx + 1 >= len(df):
            continue
        exit_result = _walk_forward_exit(
            df, entry_idx, sig["direction"],
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

    df_trades = pd.DataFrame(all_trades)
    _print_summary(df_trades, asset_type)
    return df_trades


def _print_summary(df: pd.DataFrame, asset_type: str):
    print(f"\n{'='*60}")
    print(f"STR-AH Island Reversal Phase 1A Backtest ({asset_type})")
    print(f"{'='*60}")
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
              f"avg R={s['r_multiple'].mean():.3f}, sum R={s['r_multiple'].sum():.3f}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="STR-AH Island Reversal Scanner")
    ap.add_argument("--backtest", action="store_true", help="Run Phase 1A backtest")
    ap.add_argument("--crypto", action="store_true", help="Backtest crypto instead of stocks")
    args = ap.parse_args()
    if args.backtest:
        if args.crypto:
            symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
            print("=== STR-AH Phase 1A Backtest (Crypto) ===\n")
            result = run_phase1a(symbols, "crypto")
        else:
            symbols = [
                "SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL", "META",
                "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST",
            ]
            print("=== STR-AH Phase 1A Backtest (Stocks) ===\n")
            result = run_phase1a(symbols, "stock")
            if len(result) > 0:
                out_path = Path(__file__).parent.parent / "results" / "STR-AH-stocks-phase1a.csv"
                result.to_csv(out_path, index=False)
                print(f"\nResults saved to {out_path}")
    else:
        print(__doc__)
