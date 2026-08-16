#!/usr/bin/env python3
"""
scanner_r_alligator.py
======================
HermesForge STR-R: Williams Alligator Trend Strategy

Bill Williams' Alligator indicator — three Smoothed Moving Averages (SMMA)
representing the Alligator's Jaw, Teeth, and Lips. The strategy enters when
the Alligator "wakes up" (lines fan out in aligned order) and exits when it
"goes back to sleep" (lines converge/tangle).

Indicator Parameters (Bill Williams' original):
  Jaw  (blue):  SMMA(13) of median price, shifted 8 bars forward
  Teeth (red):  SMMA(8)  of median price, shifted 5 bars forward
  Lips  (green): SMMA(5)  of median price, shifted 3 bars forward

Signal Rules:
  LONG entry:
    1. Lips > Teeth > Jaw (bullish fan order)
    2. Price closes above Lips (price is in front of the Alligator's mouth)
    3. Lines are spreading (Lips-Teeth distance increasing vs prior bar)
    4. Alligator was sleeping within last 5 bars (lines were tangled)

  SHORT entry:
    1. Lips < Teeth < Jaw (bearish fan order)
    2. Price closes below Lips
    3. Lines are spreading
    4. Alligator was sleeping within last 5 bars

  Exit:
    - Stop: 1.5 ATR(14) from entry
    - Target: 3R
    - Time stop: 20 bars
    - Also exit if Alligator goes back to sleep (lines tangle)

The "was sleeping" requirement filters out entries in mature trends where
the move may already be exhausted. We want to catch the awakening.

Dependencies: pandas, numpy
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

STRATEGY_ID = "STR-R-alligator"
STRATEGY_NAME = "Williams Alligator Trend"
STRATEGY_VERSION = "1.0"
MAX_HOLD_BARS = 20
TARGET_RR = 3.0
STOP_ATR_MULT = 1.5


def _smma(series: pd.Series, period: int) -> pd.Series:
    """Calculate Smoothed Moving Average (SMMA).
    
    SMMA is essentially an exponential moving average with alpha = 1/period.
    First value = simple average of first `period` values.
    """
    smma = series.ewm(alpha=1/period, adjust=False).mean()
    return smma


def _compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute Average True Range."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    
    return tr.ewm(alpha=1/period, adjust=False).mean()


def compute_alligator(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Williams Alligator indicator.
    
    Returns DataFrame with jaw, teeth, lips columns.
    Median price = (high + low) / 2
    
    Jaw:  SMMA(13) shifted 8 bars forward
    Teeth: SMMA(8)  shifted 5 bars forward
    Lips: SMMA(5)  shifted 3 bars forward
    """
    median_price = (df["high"] + df["low"]) / 2
    
    jaw = _smma(median_price, 13).shift(8)
    teeth = _smma(median_price, 8).shift(5)
    lips = _smma(median_price, 5).shift(3)
    
    result = df.copy()
    result["alligator_jaw"] = jaw
    result["alligator_teeth"] = teeth
    result["alligator_lips"] = lips
    
    # Spreading: distance between lines is increasing
    result["lips_teeth_gap"] = lips - teeth
    result["teeth_jaw_gap"] = teeth - jaw
    result["lips_teeth_spreading"] = result["lips_teeth_gap"] > result["lips_teeth_gap"].shift(1)
    
    # Sleeping: all three lines are within 0.5 ATR of each other (tangled)
    atr = _compute_atr(df)
    result["alligator_atr"] = atr
    line_spread = (lips - jaw).abs()
    result["alligator_sleeping"] = line_spread < (atr * 0.5)
    
    # Was sleeping within last N bars
    result["was_sleeping_5"] = result["alligator_sleeping"].rolling(5).max() > 0
    
    return result


def scan(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    """Scan for Williams Alligator signals.
    
    Returns list of signal dicts matching HermesForge scanner format.
    """
    if len(df) < 30:
        return []
    
    result = compute_alligator(df)
    
    # Drop NaN rows (from SMMA warmup and shifts)
    result = result.dropna(subset=["alligator_jaw", "alligator_teeth", "alligator_lips"])
    
    if len(result) < 5:
        return []
    
    signals = []
    
    for i in range(2, len(result)):
        row = result.iloc[i]
        prev = result.iloc[i - 1]
        
        jaw = row["alligator_jaw"]
        teeth = row["alligator_teeth"]
        lips = row["alligator_lips"]
        close = row["close"]
        atr = row["alligator_atr"]
        
        if pd.isna(atr) or atr <= 0:
            continue
        
        # Check for bullish fan: Lips > Teeth > Jaw
        bullish_fan = lips > teeth > jaw
        # Check for bearish fan: Lips < Teeth < Jaw
        bearish_fan = lips < teeth < jaw
        
        # Lines must be spreading
        spreading = row["lips_teeth_spreading"]
        
        # Was sleeping within last 5 bars (catching the awakening)
        was_sleeping = row["was_sleeping_5"]
        
        # Previous bar was NOT in a fan (newly awakened)
        prev_bullish = prev["alligator_lips"] > prev["alligator_teeth"] > prev["alligator_jaw"]
        prev_bearish = prev["alligator_lips"] < prev["alligator_teeth"] < prev["alligator_jaw"]
        
        # ── LONG signal ──
        if bullish_fan and not prev_bullish and was_sleeping and spreading:
            # Price should be above lips (in front of the mouth)
            if close > lips:
                entry_price = close
                stop_price = entry_price - (STOP_ATR_MULT * atr)
                risk = entry_price - stop_price
                target_price = entry_price + (risk * TARGET_RR)
                
                signals.append({
                    "date": result.index[i],
                    "ticker": ticker,
                    "strategy_id": STRATEGY_ID,
                    "strategy_name": STRATEGY_NAME,
                    "strategy_version": STRATEGY_VERSION,
                    "direction": "long",
                    "entry_price": entry_price,
                    "stop_price": stop_price,
                    "target_price": target_price,
                    "alligator_jaw": jaw,
                    "alligator_teeth": teeth,
                    "alligator_lips": lips,
                    "atr": atr,
                    "signal_type": "alligator_awakening_long",
                })
        
        # ── SHORT signal ──
        if not long_only and bearish_fan and not prev_bearish and was_sleeping and spreading:
            if close < lips:
                entry_price = close
                stop_price = entry_price + (STOP_ATR_MULT * atr)
                risk = stop_price - entry_price
                target_price = entry_price - (risk * TARGET_RR)
                
                signals.append({
                    "date": result.index[i],
                    "ticker": ticker,
                    "strategy_id": STRATEGY_ID,
                    "strategy_name": STRATEGY_NAME,
                    "strategy_version": STRATEGY_VERSION,
                    "direction": "short",
                    "entry_price": entry_price,
                    "stop_price": stop_price,
                    "target_price": target_price,
                    "alligator_jaw": jaw,
                    "alligator_teeth": teeth,
                    "alligator_lips": lips,
                    "atr": atr,
                    "signal_type": "alligator_awakening_short",
                })
    
    return signals


def _walk_forward_exit(df: pd.DataFrame, entry_idx: int, direction: str,
                       entry_price: float, stop_price: float, target_price: float,
                       max_bars: int = MAX_HOLD_BARS) -> dict:
    """Simulate trade exit by walking forward from entry."""
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
    
    # Time stop — also check if Alligator went back to sleep
    exit_bar = df.iloc[min(entry_idx + max_bars, n - 1)]
    exit_price = exit_bar["close"]

    # Precompute Alligator ONCE (was O(n^2): recomputed for every bar in window)
    alligator_data = compute_alligator(df)

    # Check if Alligator lines tangled during holding period
    for i in range(entry_idx + 1, min(entry_idx + max_bars + 1, n)):
        last = alligator_data.iloc[i]
        if pd.isna(last.get("alligator_sleeping")):
            continue
        if last["alligator_sleeping"]:
            exit_price = df.iloc[i]["close"]
            risk = abs(entry_price - stop_price)
            if risk > 0:
                if direction == "long":
                    r_multiple = (exit_price - entry_price) / risk
                else:
                    r_multiple = (entry_price - exit_price) / risk
            else:
                r_multiple = 0
            return {"exit_type": "sleep", "exit_price": exit_price,
                    "bars_held": i - entry_idx, "r_multiple": round(r_multiple, 3)}

    risk = entry_price - stop_price if direction == "long" else stop_price - entry_price
    r = (exit_price - entry_price) / risk if direction == "long" else (entry_price - exit_price) / risk
    if risk <= 0:
        r = 0

    return {"exit_type": "time", "exit_price": exit_price,
            "bars_held": max_bars, "r_multiple": round(r, 3)}


def run_backtest(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    """Run backtest for a single ticker. Returns list of trade results."""
    signals = scan(df, ticker, long_only=long_only)
    if not signals:
        return []
    
    trades = []
    
    for sig in signals:
        # Find the bar index for this signal
        if "date" in sig and hasattr(df.index, 'strftime'):
            try:
                target_date = pd.Timestamp(sig["date"])
                mask = df.index == target_date
                if not mask.any():
                    continue
                entry_idx = df.index.get_loc(df.index[mask][0])
            except (ValueError, KeyError, TypeError):
                continue
        else:
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
    """Run Phase 1A backtest across multiple tickers."""
    DATA_DIR = Path.home() / ".hermes" / "market_data"
    
    all_trades = []
    
    for sym in symbols:
        print(f"  Scanning {sym}...", flush=True)
        
        if asset_type == "crypto":
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "data"))
            from fetch_crypto_data import load_all as load_crypto
            crypto_data = load_crypto()
            if sym in crypto_data:
                df = crypto_data[sym]
            else:
                continue
        else:
            # Use cached stock data (parquet in ~/.hermes/market_data/)
            cache_path = DATA_DIR / f"{sym}.parquet"
            if not cache_path.exists():
                print(f"    No cached data for {sym}")
                continue
            df = pd.read_parquet(cache_path)
            # Ensure Date is the index
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
    
    df = pd.DataFrame(all_trades)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"STR-R Williams Alligator Phase 1A Backtest ({asset_type})")
    print(f"{'='*60}")
    print(f"Total signals: {len(df)}")
    print(f"Win rate: {(df['r_multiple'] > 0).mean() * 100:.1f}%")
    print(f"Average R: {df['r_multiple'].mean():.3f}")
    print(f"Median R: {df['r_multiple'].median():.3f}")
    print(f"Sum R: {df['r_multiple'].sum():.3f}")
    print(f"Max win: {df['r_multiple'].max():.3f}R")
    print(f"Max loss: {df['r_multiple'].min():.3f}R")
    print(f"Avg bars held: {df['bars_held'].mean():.1f}")
    
    # By direction
    print(f"\nBy direction:")
    for d in ["long", "short"]:
        s = df[df["direction"] == d]
        if len(s) > 0:
            print(f"  {d}: {len(s)} trades, WR={((s['r_multiple'] > 0).mean() * 100):.1f}%, "
                  f"avg R={s['r_multiple'].mean():.3f}")
    
    # By exit type
    print(f"\nBy exit type:")
    for et in ["target", "stop", "time", "sleep"]:
        s = df[df["exit_type"] == et]
        if len(s) > 0:
            print(f"  {et}: {len(s)} trades, avg R={s['r_multiple'].mean():.3f}")
    
    # Profit factor
    pos_r = df[df["r_multiple"] > 0]["r_multiple"].sum()
    neg_r = abs(df[df["r_multiple"] < 0]["r_multiple"].sum())
    pf = pos_r / neg_r if neg_r > 0 else float('inf')
    print(f"\nProfit factor: {pf:.2f}")
    
    return df


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="STR-R Williams Alligator Scanner")
    ap.add_argument("--backtest", action="store_true", help="Run Phase 1A backtest")
    ap.add_argument("--crypto", action="store_true", help="Backtest crypto instead of stocks")
    ap.add_argument("--dry-run", action="store_true", help="Just scan latest data")
    args = ap.parse_args()
    
    if args.backtest:
        if args.crypto:
            crypto_symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
            print("=== STR-R Phase 1A Backtest (Crypto) ===\n")
            result = run_phase1a(crypto_symbols, "crypto")
        else:
            stock_symbols = [
                "SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL", "META",
                "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST",
            ]
            print("=== STR-R Phase 1A Backtest (Stocks) ===\n")
            result = run_phase1a(stock_symbols, "stock")
            
            if len(result) > 0:
                out_path = Path(__file__).parent.parent.parent / "scripts" / "validation" / "results" / "STR-R-stocks-phase1a.csv"
                result.to_csv(out_path, index=False)
                print(f"\nResults saved to {out_path}")
    elif args.dry_run:
        # Scan latest cached data
        DATA_DIR = Path(__file__).parent.parent.parent / "data"
        stock_symbols = ["SPY", "QQQ", "AAPL", "NVDA", "MSFT", "GOOGL", "META"]
        print("=== STR-R Dry Run (latest data) ===\n")
        for sym in stock_symbols:
            cache_path = DATA_DIR / f"{sym}_daily.csv"
            if not cache_path.exists():
                continue
            df = pd.read_csv(cache_path, parse_dates=["Date"], index_col="Date")
            signals = scan(df, sym, long_only=True)
            if signals:
                latest = signals[-1]
                print(f"  {sym}: {latest['direction']} @ {latest['entry_price']:.2f} "
                      f"stop={latest['stop_price']:.2f} target={latest['target_price']:.2f} "
                      f"({latest['signal_type']})")
            else:
                print(f"  {sym}: no signal")
    else:
        print(__doc__)
