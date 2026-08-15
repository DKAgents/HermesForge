#!/usr/bin/env python3
"""
scanner_q_liquidity_sweep.py
=============================
HermesForge US-107 — STR-Q: Liquidity Sweep Reversal Strategy

Phase 1A validation scanner for the liquidity sweep detection engine.
Walks through historical intraday data, detects sweeps, and simulates trades.

Signal Rules:
  1. Detect liquidity sweep at key level (PDH/PDL, equal highs/lows, 
     swing high/low, round number, session high/low)
  2. Price penetrates beyond level (min 0.15 ATR)
  3. Price closes back on opposite side (reversal confirmation)
  4. Wick ratio >= 0.5 (long wick relative to body)
  5. Confirmation: subsequent bars don't reclaim the swept level
  
  LONG (bullish sweep): Price sweeps BELOW support, reverses UP
    Entry: close of sweep candle
    Stop: sweep low - 0.1 * ATR (behind the wick)
    Target: 3R or next resistance level
    
  SHORT (bearish sweep): Price sweeps ABOVE resistance, reverses DOWN
    Entry: close of sweep candle
    Stop: sweep high + 0.1 * ATR (behind the wick)
    Target: 3R or next support level

Exit simulation:
  - target: price hits 3R
  - stop: price hits stop
  - time: 15 bars (75 min on 5m, 3.75h on 15m)

Dependencies: pandas, numpy, Hyperliquid API (crypto), yfinance (stocks)
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

MODULE_DIR = Path(__file__).parent
DATA_DIR = Path(__file__).parent.parent.parent / "data"
sys.path.insert(0, str(DATA_DIR))

from detect_liquidity_sweeps import (
    LiquidityLevel, SweepEvent, _compute_atr, _find_swing_highs, 
    _find_swing_lows, _find_equal_levels, _find_round_numbers,
    identify_liquidity_levels, detect_sweep_at_level,
    SWEEP_PENETRATION_ATR, MAX_SWEEP_DEPTH_ATR, MIN_WICK_RATIO,
    CONFIRMATION_BARS, STOP_BUFFER_ATR, MIN_VOLUME_SURGE,
)
from fetch_intraday_crypto import get_intraday_candles, get_daily_levels as get_crypto_daily_levels
from fetch_intraday_stocks import get_intraday_bars, get_daily_levels as get_stock_daily_levels, get_session_levels

STRATEGY_ID = "Q_LIQUIDITY_SWEEP"
MAX_HOLD_BARS = 15
TARGET_RR = 3.0
MIN_QUALITY_SCORE = 40


def _walk_forward_exit(df: pd.DataFrame, entry_idx: int, direction: str,
                       entry_price: float, stop_price: float, target_price: float,
                       max_bars: int = MAX_HOLD_BARS) -> dict:
    """
    Simulate trade exit by walking forward from entry.
    
    Returns dict with exit_type, exit_price, bars_held, r_multiple.
    """
    n = len(df)
    
    for i in range(entry_idx + 1, min(entry_idx + max_bars + 1, n)):
        bar = df.iloc[i]
        
        if direction == "bullish":
            # Check stop first (conservative: assume worst case)
            if bar["low"] <= stop_price:
                return {
                    "exit_type": "stop",
                    "exit_price": stop_price,
                    "bars_held": i - entry_idx,
                    "r_multiple": -1.0,
                }
            # Check target
            if bar["high"] >= target_price:
                return {
                    "exit_type": "target",
                    "exit_price": target_price,
                    "bars_held": i - entry_idx,
                    "r_multiple": TARGET_RR,
                }
        else:  # bearish
            if bar["high"] >= stop_price:
                return {
                    "exit_type": "stop",
                    "exit_price": stop_price,
                    "bars_held": i - entry_idx,
                    "r_multiple": -1.0,
                }
            if bar["low"] <= target_price:
                return {
                    "exit_type": "target",
                    "exit_price": target_price,
                    "bars_held": i - entry_idx,
                    "r_multiple": TARGET_RR,
                }
    
    # Time stop
    last_bar = df.iloc[min(entry_idx + max_bars, n - 1)]
    exit_price = last_bar["close"]
    if direction == "bullish":
        risk = entry_price - stop_price
        r = (exit_price - entry_price) / risk if risk > 0 else 0
    else:
        risk = stop_price - entry_price
        r = (entry_price - exit_price) / risk if risk > 0 else 0
    
    return {
        "exit_type": "time",
        "exit_price": exit_price,
        "bars_held": max_bars,
        "r_multiple": round(r, 3),
    }


def scan_ticker_intraday(
    symbol: str,
    interval: str = "5m",
    asset_type: str = "crypto",
    lookback_bars: int = 500,
) -> list:
    """
    Scan a single ticker for historical sweep signals and simulate trades.
    
    Walks through historical intraday bars, detects sweeps at each bar,
    and simulates trades with entry/stop/target/time stop.
    
    Returns list of trade result dicts.
    """
    # Fetch data
    if asset_type == "crypto":
        df = get_intraday_candles(symbol, interval, lookback_bars)
        daily_levels = get_crypto_daily_levels(symbol)
        session_levels = {}
    else:
        df = get_intraday_bars(symbol, interval, lookback_bars)
        daily_levels = get_stock_daily_levels(symbol)
        session_levels = get_session_levels(symbol, interval)
    
    if len(df) < 50:
        return []
    
    # Compute ATR
    atr = _compute_atr(df)
    
    trades = []
    used_ranges = set()  # Track entry bar ranges to avoid duplicate trades
    
    # Walk through each bar (skip first/last 20 for context)
    for i in range(20, len(df) - MAX_HOLD_BARS - 1):
        # Use a sliding window of data up to current bar
        window = df.iloc[:i+1].tail(lookback_bars).reset_index(drop=True)
        window_atr = atr.iloc[:i+1].tail(lookback_bars).reset_index(drop=True)
        
        if len(window) < 30:
            continue
        
        current_price = window["close"].iloc[-1]
        
        # Identify liquidity levels
        levels = identify_liquidity_levels(
            window, daily_levels, session_levels, current_price
        )
        
        if not levels:
            continue
        
        # Check top 5 most relevant levels for sweeps
        for level in levels[:5]:
            sweep = detect_sweep_at_level(
                window, level, window_atr, symbol, interval, asset_type,
                lookback=15,
            )
            
            if sweep is None:
                continue
            
            if sweep.quality_score < MIN_QUALITY_SCORE:
                continue
            
            if sweep.confirmation != "confirmed":
                continue
            
            # Check we haven't already traded this sweep
            sweep_time = sweep.timestamp
            if sweep_time in used_ranges:
                continue
            
            # Find the entry bar index in the full dataframe
            entry_bar_time = pd.Timestamp(sweep_time)
            entry_mask = df["timestamp"] == entry_bar_time
            if not entry_mask.any():
                continue
            
            entry_idx = df.index[entry_mask][0]
            
            # Skip if not enough bars for exit simulation
            if entry_idx + MAX_HOLD_BARS >= len(df):
                continue
            
            # Simulate trade
            exit_result = _walk_forward_exit(
                df, entry_idx, sweep.direction,
                sweep.entry_price, sweep.stop_price, sweep.target_price,
            )
            
            # Record trade
            trade = {
                "symbol": symbol,
                "strategy": STRATEGY_ID,
                "asset_type": asset_type,
                "interval": interval,
                "date": str(entry_bar_time),
                "direction": sweep.direction,
                "level_type": sweep.level_type,
                "level_price": round(sweep.level_price, 4),
                "entry_price": round(sweep.entry_price, 4),
                "stop_price": round(sweep.stop_price, 4),
                "target_price": round(sweep.target_price, 4),
                "exit_type": exit_result["exit_type"],
                "exit_price": round(exit_result["exit_price"], 4),
                "bars_held": exit_result["bars_held"],
                "r_multiple": exit_result["r_multiple"],
                "quality_score": sweep.quality_score,
                "penetration_atr": round(sweep.penetration_atr, 3),
                "wick_ratio": round(sweep.wick_ratio, 3),
                "volume_surge": round(sweep.volume_surge, 3),
                "risk_reward": sweep.risk_reward,
            }
            
            trades.append(trade)
            used_ranges.add(sweep_time)
            
            # Skip ahead past this trade's holding period
            break  # Only take one signal per bar
    
    return trades


def run_backtest(
    symbols: list,
    interval: str = "5m",
    asset_type: str = "crypto",
    lookback_bars: int = 500,
) -> pd.DataFrame:
    """
    Run Phase 1A backtest across multiple tickers.
    
    Returns DataFrame with all simulated trades.
    """
    all_trades = []
    
    for sym in symbols:
        print(f"  Scanning {sym}...")
        trades = scan_ticker_intraday(sym, interval, asset_type, lookback_bars)
        all_trades.extend(trades)
        print(f"    {len(trades)} signals found")
    
    if not all_trades:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_trades)
    
    # Summary stats
    print(f"\n{'='*60}")
    print(f"STR-Q Phase 1A Backtest Results ({asset_type} {interval})")
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
    for direction in ["bullish", "bearish"]:
        subset = df[df["direction"] == direction]
        if len(subset) > 0:
            print(f"  {direction}: {len(subset)} trades, WR={((subset['r_multiple'] > 0).mean() * 100):.1f}%, "
                  f"avg R={subset['r_multiple'].mean():.3f}")
    
    # By level type
    print(f"\nBy level type:")
    for lt in df["level_type"].unique():
        subset = df[df["level_type"] == lt]
        if len(subset) >= 3:
            print(f"  {lt}: {len(subset)} trades, WR={((subset['r_multiple'] > 0).mean() * 100):.1f}%, "
                  f"avg R={subset['r_multiple'].mean():.3f}")
    
    # By exit type
    print(f"\nBy exit type:")
    for et in ["target", "stop", "time"]:
        subset = df[df["exit_type"] == et]
        if len(subset) > 0:
            print(f"  {et}: {len(subset)} trades, avg R={subset['r_multiple'].mean():.3f}")
    
    # By quality score bucket
    print(f"\nBy quality score:")
    for low, high in [(40, 50), (50, 60), (60, 70), (70, 80), (80, 100)]:
        subset = df[(df["quality_score"] >= low) & (df["quality_score"] < high)]
        if len(subset) >= 3:
            print(f"  {low}-{high}: {len(subset)} trades, WR={((subset['r_multiple'] > 0).mean() * 100):.1f}%, "
                  f"avg R={subset['r_multiple'].mean():.3f}")
    
    return df


if __name__ == "__main__":
    print("=== STR-Q Phase 1A Backtest ===\n")
    
    # Crypto backtest
    print("── CRYPTO (Hyperliquid 5m) ──")
    crypto_symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
    crypto_df = run_backtest(crypto_symbols, "5m", "crypto", lookback_bars=500)
    
    print("\n")
    
    # Stock backtest
    print("── STOCKS (yfinance 5m) ──")
    stock_symbols = ["SPY", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL", "META"]
    stock_df = run_backtest(stock_symbols, "5m", "stock", lookback_bars=500)
    
    # Save results
    if len(crypto_df) > 0:
        crypto_df.to_csv(DATA_DIR.parent / "scripts" / "validation" / "results" / "STR-Q-crypto-phase1a.csv", index=False)
        print(f"\nCrypto results saved.")
    if len(stock_df) > 0:
        stock_df.to_csv(DATA_DIR.parent / "scripts" / "validation" / "results" / "STR-Q-stocks-phase1a.csv", index=False)
        print(f"Stock results saved.")
