#!/usr/bin/env python3
"""
scanner_y_adx_dmi.py
====================
HermesForge STR-Y: ADX/DMI Directional Movement Strategy (v3.0 — structure-based)

Compute ADX(14), +DI(14), -DI(14) using Wilder smoothing.

Signal Rules (UNCHANGED — ADX/DMI is the SIGNAL TRIGGER only):
  LONG entry:  +DI crosses above -DI AND ADX > 22 (trending up).
  SHORT entry: -DI crosses above +DI AND ADX > 22 (trending down).
  Exit signal: opposite DI cross (handled via time-stop / mechanical exits here).

v3.0 (US-115): entry / stop / target are now derived from market structure via
the shared market_structure.compute_structure_trade module. This OVERRIDES the
previous fixed stop; the ADX/DMI cross remains the trigger, structure determines
stop/target.
  - Entry : pullback to nearest confirmed support, up to 5-bar wait.
  - Stop  : nearest confirmed swing low below entry, ATR-buffered, capped 2 ATR.
  - Target: nearest confirmed overhead resistance with R >= 1.5; skip if none.
  - Cooldown: 20-bar per-ticker guard after each accepted signal.
  - Exit walk starts at the actual entry_idx. Target R is dynamic.
  - Time stop: 20 bars (unchanged).

Version history:
  1.0 — original (entry=close, stop=2 ATR, target=3R).
  2.0 — US-114 optimization (ADX_THRESHOLD=22, STOP_ATR_MULT=1.0, target=3R).
  3.0 — US-115 structure-based entry/stop/target (this version). The fixed
        STOP_ATR_MULT / TARGET_RR constants are removed; structure decides.

Long-only for stocks.

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

STRATEGY_ID = "STR-Y-adx-dmi"
STRATEGY_NAME = "ADX/DMI Directional Movement"
STRATEGY_VERSION = "3.0"
MAX_HOLD_BARS = 20
COOLDOWN_BARS = 20
ADX_PERIOD = 14
ADX_THRESHOLD = 22.0


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
    """Scan for ADX/DMI cross signals (structure-based entry/stop/target)."""
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
    atr_series = indicators["atr"]  # Series aligned to df
    close_arr = df["close"].values.astype(float)

    signals = []
    min_start = ADX_PERIOD * 2 + 1
    last_trade_idx = -COOLDOWN_BARS  # per-ticker cooldown

    for i in range(min_start, len(df)):
        if (np.isnan(adx[i]) or np.isnan(adx[i - 1]) or
                np.isnan(plus_di[i]) or np.isnan(minus_di[i]) or
                np.isnan(plus_di[i - 1]) or np.isnan(minus_di[i - 1]) or
                np.isnan(atr_series.iloc[i])):
            continue

        # Cooldown guard: skip signals too close to the last accepted trade.
        if i - last_trade_idx < COOLDOWN_BARS:
            continue

        # +DI crosses above -DI (bullish cross)
        plus_cross_up = plus_di[i - 1] <= minus_di[i - 1] and plus_di[i] > minus_di[i]
        # -DI crosses above +DI (bearish cross)
        minus_cross_up = minus_di[i - 1] <= plus_di[i - 1] and minus_di[i] > plus_di[i]

        trending = adx[i] > ADX_THRESHOLD

        # LONG
        if plus_cross_up and trending:
            trade = compute_structure_trade(
                df, signal_idx=i, direction="long",
                max_wait_bars=5, min_rr=1.5, max_atr=2.0,
                atr=atr_series, entry_fallback="signal",
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
                "adx": round(adx[i], 2),
                "plus_di": round(plus_di[i], 2),
                "minus_di": round(minus_di[i], 2),
                "signal_type": "di_bullish_cross",
            })
            last_trade_idx = i

        # SHORT
        if not long_only and minus_cross_up and trending:
            trade = compute_structure_trade(
                df, signal_idx=i, direction="short",
                max_wait_bars=5, min_rr=1.5, max_atr=2.0,
                atr=atr_series, entry_fallback="signal",
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
                "adx": round(adx[i], 2),
                "plus_di": round(plus_di[i], 2),
                "minus_di": round(minus_di[i], 2),
                "signal_type": "di_bearish_cross",
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
        # Use the structure-derived entry_idx (pullback may fill after signal).
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
        entry_idx = int(entry_idx)
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
            "entry_date": sig.get("entry_date", sig["date"]),
            "entry_idx": entry_idx,
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
