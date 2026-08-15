#!/usr/bin/env python3
"""
fetch_intraday_crypto.py
========================
HermesForge US-107 — Intraday crypto data from Hyperliquid API.

Provides 1m, 5m, 15m, 1h candles for sweep detection and intraday analysis.
Free, no API key required, unlimited historical data.

Data format per candle:
  t  — open time (ms epoch)
  T  — close time (ms epoch)
  o  — open
  c  — close
  h  — high
  l  — low
  v  — volume (base asset)
  n  — number of trades

Caching:
  Parquet files stored in ~/.hermes/market_data/intraday/crypto/
  Filename: {SYMBOL}_{interval}.parquet
  TTL: 1m=5min, 5m=15min, 15m=30min, 1h=2h

Usage:
  from fetch_intraday_crypto import get_intraday_candles
  df = get_intraday_candles('BTC', interval='5m', lookback_bars=500)
"""

import os
import sys
import time
import json
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta, timezone

MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

CACHE_DIR = Path.home() / ".hermes" / "market_data" / "intraday" / "crypto"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

HYPERLIQUID_API = "https://api.hyperliquid.xyz/info"

# TTL per interval (seconds)
INTERVAL_TTL = {
    "1m": 300,      # 5 minutes
    "5m": 900,      # 15 minutes
    "15m": 1800,    # 30 minutes
    "1h": 7200,     # 2 hours
}

# Max bars per API call (Hyperliquid returns ~500 max)
MAX_BARS_PER_CALL = 500


def _cache_path(symbol: str, interval: str) -> Path:
    """Return cache file path for symbol + interval."""
    return CACHE_DIR / f"{symbol.upper()}_{interval}.parquet"


def _is_cache_valid(symbol: str, interval: str) -> bool:
    """Check if cached data is still fresh."""
    path = _cache_path(symbol, interval)
    if not path.exists():
        return False
    ttl = INTERVAL_TTL.get(interval, 900)
    age = time.time() - path.stat().st_mtime
    return age < ttl


def _fetch_candles_api(symbol: str, interval: str, start_ms: int, end_ms: int) -> list:
    """Fetch candles from Hyperliquid API."""
    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": symbol.upper(),
            "interval": interval,
            "startTime": start_ms,
            "endTime": end_ms,
        }
    }
    try:
        r = requests.post(HYPERLIQUID_API, json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"  [WARN] Hyperliquid fetch failed for {symbol} {interval}: {e}")
        return []


def _parse_candles(raw: list, symbol: str, interval: str) -> pd.DataFrame:
    """Parse raw API response into DataFrame."""
    if not raw:
        return pd.DataFrame()
    
    rows = []
    for c in raw:
        rows.append({
            "timestamp": pd.Timestamp(c["t"], unit="ms", tz="UTC"),
            "open": float(c["o"]),
            "high": float(c["h"]),
            "low": float(c["l"]),
            "close": float(c["c"]),
            "volume": float(c["v"]),
            "trades": int(c["n"]),
            "symbol": symbol.upper(),
            "interval": interval,
        })
    
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def get_intraday_candles(
    symbol: str,
    interval: str = "5m",
    lookback_bars: int = 500,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Fetch intraday candles for a crypto symbol.
    
    Args:
        symbol: Crypto symbol (e.g. 'BTC', 'ETH', 'SOL')
        interval: '1m', '5m', '15m', '1h'
        lookback_bars: Number of bars to fetch (max 500 per call, will paginate)
        use_cache: Whether to use cached data
        
    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume, trades, symbol, interval
    """
    symbol = symbol.upper()
    
    # Try cache
    if use_cache and _is_cache_valid(symbol, interval):
        df = pd.read_parquet(_cache_path(symbol, interval))
        if len(df) >= lookback_bars:
            return df.tail(lookback_bars).reset_index(drop=True)
    
    # Calculate time range
    interval_seconds = {
        "1m": 60, "5m": 300, "15m": 900, "1h": 3600
    }
    sec_per_bar = interval_seconds.get(interval, 300)
    now_ms = int(time.time() * 1000)
    
    # Fetch in batches if needed
    all_candles = []
    bars_remaining = lookback_bars
    end_ms = now_ms
    
    while bars_remaining > 0:
        batch_size = min(bars_remaining, MAX_BARS_PER_CALL)
        start_ms = end_ms - (batch_size * sec_per_bar * 1000)
        
        raw = _fetch_candles_api(symbol, interval, start_ms, end_ms)
        if not raw:
            break
        
        all_candles = raw + all_candles  # prepend older candles
        bars_remaining -= len(raw)
        
        if len(raw) < batch_size:
            break  # no more data available
        
        end_ms = start_ms  # move window back
    
    # Deduplicate
    seen = set()
    unique = []
    for c in all_candles:
        if c["t"] not in seen:
            seen.add(c["t"])
            unique.append(c)
    
    df = _parse_candles(unique, symbol, interval)
    
    # Cache
    if len(df) > 0:
        df.to_parquet(_cache_path(symbol, interval), index=False)
    
    return df


def get_multi_symbol_candles(
    symbols: list,
    interval: str = "5m",
    lookback_bars: int = 500,
) -> dict:
    """
    Fetch intraday candles for multiple symbols.
    
    Returns:
        Dict mapping symbol -> DataFrame
    """
    result = {}
    for sym in symbols:
        df = get_intraday_candles(sym, interval, lookback_bars)
        if len(df) > 0:
            result[sym] = df
    return result


def get_daily_levels(symbol: str) -> dict:
    """
    Get prior day high/low/current day open for sweep level detection.
    
    Returns:
        {'prior_high': float, 'prior_low': float, 'prior_close': float,
         'current_open': float, 'current_high': float, 'current_low': float}
    """
    # Fetch daily candles (1h interval, aggregate)
    df = get_intraday_candles(symbol, "1h", lookback_bars=48)
    if len(df) < 24:
        return {}
    
    # Group by UTC date
    df["date"] = df["timestamp"].dt.date
    daily = df.groupby("date").agg({
        "open": "first", "high": "max", "low": "min", "close": "last"
    }).reset_index()
    
    if len(daily) < 2:
        return {}
    
    prior = daily.iloc[-2]
    current = daily.iloc[-1]
    
    return {
        "prior_high": float(prior["high"]),
        "prior_low": float(prior["low"]),
        "prior_close": float(prior["close"]),
        "current_open": float(current["open"]),
        "current_high": float(current["high"]),
        "current_low": float(current["low"]),
        "prior_date": str(prior["date"]),
        "current_date": str(current["date"]),
    }


if __name__ == "__main__":
    # Test
    print("=== Testing Hyperliquid Intraday Data ===\n")
    
    for sym in ["BTC", "ETH", "SOL"]:
        for interval in ["5m", "15m"]:
            df = get_intraday_candles(sym, interval, lookback_bars=100)
            if len(df) > 0:
                print(f"{sym} {interval}: {len(df)} bars")
                print(f"  Range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
                print(f"  Last close: ${df['close'].iloc[-1]:,.2f}")
                print()
    
    print("=== Daily Levels ===")
    levels = get_daily_levels("BTC")
    for k, v in levels.items():
        print(f"  {k}: {v}")
