#!/usr/bin/env python3
"""
scanner_ad_keltner.py
=====================
HermesForge STR-AD: Keltner Channel Breakout Strategy (v2.0 — structure-based)

Keltner Channel:
  Middle = EMA(20)
  Upper  = EMA(20) + 2 * ATR(10)
  Lower  = EMA(20) - 2 * ATR(10)

Signal Rules (UNCHANGED — indicator logic is the trigger only):
  LONG:  price closes above upper band (breakout up)
  SHORT: price closes below lower band (breakout down)

v2.0 (US-115): entry / stop / target are now derived from market structure via
the shared market_structure.compute_structure_trade module, NOT from fixed
parameters.
  - Entry : pullback to nearest confirmed support below the breakout close
            (limit order, up to 5-bar wait), else market at signal close.
  - Stop  : nearest confirmed swing low below entry, ATR-buffered, capped at
            2.0 x ATR(10).
  - Target: nearest confirmed overhead resistance offering R >= 1.5, else
            ATR-fallback target; skip the signal if none qualifies.
  - Cooldown: 20-bar per-ticker guard after each accepted signal.
  - Exit walk starts at the actual entry_idx (pullback may fill after signal).
  - Target R is dynamic (computed from entry/stop/target), not a fixed 3R.

Long-only for stocks (only LONG signals fire).

Dependencies: pandas, numpy, scipy (via market_structure)
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Sibling import of the shared market_structure module (same directory).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from market_structure import compute_structure_trade

STRATEGY_ID = "STR-AD-keltner"
STRATEGY_NAME = "Keltner Channel Breakout"
STRATEGY_VERSION = "2.0"
MAX_HOLD_BARS = 20
COOLDOWN_BARS = 20
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
    """Scan for Keltner Channel breakout signals (structure-based entry/stop/target)."""
    if len(df) < EMA_PERIOD + ATR_PERIOD + 5:
        return []
    # Keep positional alignment with df: do NOT dropna (warmup NaN rows are
    # skipped by the per-bar guard below). This guarantees entry_idx computed
    # against `res` matches positions in `df` used by run_backtest.
    res = compute_keltner(df)
    if len(res) < 5:
        return []

    atr_series = res["kc_atr"]
    signals = []
    last_trade_idx = -COOLDOWN_BARS  # per-ticker cooldown

    for i in range(1, len(res)):
        row = res.iloc[i]
        prev = res.iloc[i - 1]
        close = row["close"]
        upper = row["kc_upper"]
        lower = row["kc_lower"]
        ema = row["kc_ema"]
        atr = row["kc_atr"]
        if pd.isna(atr) or atr <= 0 or pd.isna(upper) or pd.isna(lower):
            continue

        # Cooldown guard: skip signals too close to the last accepted trade.
        if i - last_trade_idx < COOLDOWN_BARS:
            continue

        # Only fire on a fresh breakout (prev close was inside the band)
        prev_close = prev["close"]
        prev_upper = prev["kc_upper"]
        prev_lower = prev["kc_lower"]

        # LONG: close above upper band, prev close was at/below upper
        if close > upper and prev_close <= prev_upper:
            trade = compute_structure_trade(
                res, signal_idx=i, direction="long",
                max_wait_bars=5, min_rr=1.5, max_atr=2.0,
                atr=atr_series, entry_fallback="signal",
            )
            if trade is None:
                continue
            signals.append({
                "date": row.name,
                "entry_date": res.index[trade["entry_idx"]],
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
                "kc_upper": upper,
                "kc_ema": ema,
                "atr": atr,
                "signal_type": "keltner_breakout_long",
            })
            last_trade_idx = i

        # SHORT: close below lower band, prev close was at/above lower
        if not long_only and close < lower and prev_close >= prev_lower:
            trade = compute_structure_trade(
                res, signal_idx=i, direction="short",
                max_wait_bars=5, min_rr=1.5, max_atr=2.0,
                atr=atr_series, entry_fallback="signal",
            )
            if trade is None:
                continue
            signals.append({
                "date": row.name,
                "entry_date": res.index[trade["entry_idx"]],
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
                "kc_lower": lower,
                "kc_ema": ema,
                "atr": atr,
                "signal_type": "keltner_breakout_short",
            })
            last_trade_idx = i

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
        r = ((exit_price - entry_price) / risk) if direction == "long" else ((entry_price - exit_price) / risk)
    return {"exit_type": "time", "exit_price": exit_price,
            "bars_held": exit_idx - entry_idx, "r_multiple": round(r, 3)}


def run_backtest(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    signals = scan(df, ticker, long_only=long_only)
    if not signals:
        return []
    trades = []
    for sig in signals:
        # Use the structure-derived entry_idx (pullback may fill after signal).
        entry_idx = sig.get("entry_idx")
        if entry_idx is None:
            try:
                target_date = pd.Timestamp(sig["date"])
                entry_idx = df.index.get_loc(df.index[df.index == target_date][0])
            except (KeyError, ValueError, IndexError, TypeError):
                continue
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
            "entry_date": sig.get("entry_date", sig["date"]),
            "entry_idx": int(entry_idx),
            "entry_price": round(sig["entry_price"], 4),
            "stop_price": round(sig["stop_price"], 4),
            "target_price": round(sig["target_price"], 4),
            "exit_type": exit_result["exit_type"],
            "exit_price": round(exit_result["exit_price"], 4),
            "bars_held": exit_result["bars_held"],
            "r_multiple": exit_result["r_multiple"],
            "entry_type": sig.get("entry_type", "market"),
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
