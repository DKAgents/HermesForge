#!/usr/bin/env python3
"""
scanner_ad_keltner.py
=====================
HermesForge STR-AD: Keltner Channel Breakout Strategy

Keltner Channel:
  Middle = EMA(20)
  Upper  = EMA(20) + 2 * ATR(10)
  Lower  = EMA(20) - 2 * ATR(10)

Signal Rules:
  LONG:  price closes above upper band (breakout up)
  SHORT: price closes below lower band (breakout down)

Entry on breakout bar close.
Stop: middle band (EMA(20)).
Target: 3R.
Time stop: 20 bars.

Long-only for stocks (only LONG signals fire).

Dependencies: pandas, numpy
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

STRATEGY_ID = "STR-AD-keltner"
STRATEGY_NAME = "Keltner Channel Breakout"
STRATEGY_VERSION = "1.0"
MAX_HOLD_BARS = 20
TARGET_RR = 3.0
EMA_PERIOD = 20
ATR_PERIOD = 10
ATR_MULT = 2.0


def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def compute_keltner(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Keltner Channel bands."""
    close = df["close"]
    ema = _ema(close, EMA_PERIOD)
    atr = _atr(df, ATR_PERIOD)
    upper = ema + ATR_MULT * atr
    lower = ema - ATR_MULT * atr
    out = df.copy()
    out["kc_ema"] = ema
    out["kc_atr"] = atr
    out["kc_upper"] = upper
    out["kc_lower"] = lower
    return out


def scan(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    """Scan for Keltner Channel breakout signals."""
    if len(df) < EMA_PERIOD + ATR_PERIOD + 5:
        return []
    res = compute_keltner(df).dropna(subset=["kc_ema", "kc_upper", "kc_lower", "kc_atr"])
    if len(res) < 5:
        return []

    signals = []
    for i in range(1, len(res)):
        row = res.iloc[i]
        prev = res.iloc[i - 1]
        close = row["close"]
        upper = row["kc_upper"]
        lower = row["kc_lower"]
        ema = row["kc_ema"]
        atr = row["kc_atr"]
        if pd.isna(atr) or atr <= 0:
            continue

        # Only fire on a fresh breakout (prev close was inside the band)
        prev_close = prev["close"]
        prev_upper = prev["kc_upper"]
        prev_lower = prev["kc_lower"]

        # LONG: close above upper band, prev close was at/below upper
        if close > upper and prev_close <= prev_upper:
            entry_price = close
            stop_price = ema
            risk = entry_price - stop_price
            if risk <= 0:
                continue
            target_price = entry_price + risk * TARGET_RR
            signals.append({
                "date": row.name,
                "ticker": ticker,
                "strategy_id": STRATEGY_ID,
                "strategy_name": STRATEGY_NAME,
                "strategy_version": STRATEGY_VERSION,
                "direction": "long",
                "entry_price": entry_price,
                "stop_price": stop_price,
                "target_price": target_price,
                "kc_upper": upper,
                "kc_ema": ema,
                "atr": atr,
                "signal_type": "keltner_breakout_long",
            })

        # SHORT: close below lower band, prev close was at/above lower
        if not long_only and close < lower and prev_close >= prev_lower:
            entry_price = close
            stop_price = ema
            risk = stop_price - entry_price
            if risk <= 0:
                continue
            target_price = entry_price - risk * TARGET_RR
            signals.append({
                "date": row.name,
                "ticker": ticker,
                "strategy_id": STRATEGY_ID,
                "strategy_name": STRATEGY_NAME,
                "strategy_version": STRATEGY_VERSION,
                "direction": "short",
                "entry_price": entry_price,
                "stop_price": stop_price,
                "target_price": target_price,
                "kc_lower": lower,
                "kc_ema": ema,
                "atr": atr,
                "signal_type": "keltner_breakout_short",
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
    print(f"STR-AD Keltner Channel Breakout Phase 1A Backtest ({asset_type})")
    print(f"{'='*60}")
    print(f"Total signals: {len(df)}")
    print(f"Win rate: {(df['r_multiple'] > 0).mean() * 100:.1f}%")
    print(f"Average R: {df['r_multiple'].mean():.3f}")
    print(f"Median R: {df['r_multiple'].median():.3f}")
    print(f"Sum R: {df['r_multiple'].sum():.3f}")
    print(f"Max win: {df['r_multiple'].max():3f}R")
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
    # By symbol
    print(f"\nBy symbol:")
    for sym in sorted(df["symbol"].unique()):
        s = df[df["symbol"] == sym]
        print(f"  {sym}: {len(s)} trades, WR={((s['r_multiple'] > 0).mean() * 100):.1f}%, "
              f"avg R={s['r_multiple'].mean():.3f}, sum R={s['r_multiple'].sum():.3f}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="STR-AD Keltner Channel Breakout Scanner")
    ap.add_argument("--backtest", action="store_true", help="Run Phase 1A backtest")
    ap.add_argument("--crypto", action="store_true", help="Backtest crypto instead of stocks")
    args = ap.parse_args()
    if args.backtest:
        if args.crypto:
            symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
            print("=== STR-AD Phase 1A Backtest (Crypto) ===\n")
            result = run_phase1a(symbols, "crypto")
        else:
            symbols = [
                "SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL", "META",
                "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST",
            ]
            print("=== STR-AD Phase 1A Backtest (Stocks) ===\n")
            result = run_phase1a(symbols, "stock")
            if len(result) > 0:
                out_path = Path(__file__).parent.parent / "results" / "STR-AD-stocks-phase1a.csv"
                result.to_csv(out_path, index=False)
                print(f"\nResults saved to {out_path}")
    else:
        print(__doc__)
