#!/usr/bin/env python3
"""
fetch_intraday_stocks.py
========================
HermesForge US-107 — Intraday stock data from yfinance (free).

Provides 1m, 5m, 15m, 30m, 60m bars for sweep detection.
Free, no API key required.

Limitations (yfinance free tier):
  - 1m data: ~7 days history
  - 5m data: ~60 days history
  - 15m data: ~60 days history
  - 30m data: ~60 days history
  - 60m data: ~730 days history

UPGRADE PATH: If Alpaca API keys are set in .env (ALPACA_API_KEY, 
ALPACA_API_SECRET), this module will use Alpaca for 7+ years of 1m 
history. Sign up free at https://alpaca.markets

Caching:
  Parquet files stored in ~/.hermes/market_data/intraday/stocks/
  Filename: {SYMBOL}_{interval}.parquet
  TTL: 1m=5min, 5m=15min, 15m=30min, 1h=2h

Usage:
  from fetch_intraday_stocks import get_intraday_bars
  df = get_intraday_bars('AAPL', interval='5m', lookback_bars=500)
"""

import os
import sys
import time
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

CACHE_DIR = Path.home() / ".hermes" / "market_data" / "intraday" / "stocks"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Check for Alpaca keys (upgrade path)
ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY", "")
ALPACA_API_SECRET = os.environ.get("ALPACA_API_SECRET", "")
ALPACA_BASE_URL = "https://data.alpaca.markets/v2"

USE_ALPACA = bool(ALPACA_API_KEY and ALPACA_API_SECRET)

INTERVAL_TTL = {
    "1m": 300,      # 5 minutes
    "5m": 900,      # 15 minutes
    "15m": 1800,    # 30 minutes
    "30m": 1800,    # 30 minutes
    "60m": 7200,    # 2 hours
    "1h": 7200,
}

# yfinance period limits per interval
YFINANCE_PERIOD = {
    "1m": "5d",
    "5m": "60d",
    "15m": "60d",
    "30m": "60d",
    "60m": "730d",
    "1h": "730d",
}


def _cache_path(symbol: str, interval: str) -> Path:
    return CACHE_DIR / f"{symbol.upper()}_{interval}.parquet"


def _is_cache_valid(symbol: str, interval: str) -> bool:
    path = _cache_path(symbol, interval)
    if not path.exists():
        return False
    ttl = INTERVAL_TTL.get(interval, 900)
    age = time.time() - path.stat().st_mtime
    return age < ttl


def _fetch_yfinance(symbol: str, interval: str, period: str = None) -> pd.DataFrame:
    """Fetch intraday bars from yfinance."""
    import yfinance as yf
    
    if period is None:
        period = YFINANCE_PERIOD.get(interval, "60d")
    
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df is None or len(df) == 0:
            return pd.DataFrame()
        
        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Standardize column names
        df = df.rename(columns={
            "Open": "open", "High": "high", "Low": "low",
            "Close": "close", "Volume": "volume",
        })
        
        # Ensure timestamp column
        df.index.name = "timestamp"
        df = df.reset_index()
        
        # Keep only needed columns
        cols = ["timestamp", "open", "high", "low", "close", "volume"]
        df = df[[c for c in cols if c in df.columns]]
        
        # Add metadata
        df["symbol"] = symbol.upper()
        df["interval"] = interval
        
        return df
    except Exception as e:
        print(f"  [WARN] yfinance fetch failed for {symbol} {interval}: {e}")
        return pd.DataFrame()


def _fetch_alpaca(symbol: str, interval: str, lookback_bars: int = 500) -> pd.DataFrame:
    """Fetch intraday bars from Alpaca (requires API keys)."""
    import requests
    
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_API_SECRET,
    }
    
    # Map interval to Alpaca timeframe
    timeframe_map = {
        "1m": "1Min", "5m": "5Min", "15m": "15Min",
        "30m": "30Min", "60m": "1Hour", "1h": "1Hour",
    }
    timeframe = timeframe_map.get(interval, "5Min")
    
    # Calculate start time
    interval_minutes = {
        "1m": 1, "5m": 5, "15m": 15, "30m": 30, "60m": 60, "1h": 60,
    }
    mins = interval_minutes.get(interval, 5)
    start = (datetime.utcnow() - timedelta(minutes=mins * lookback_bars * 1.2)).isoformat()
    
    url = f"{ALPACA_BASE_URL}/stocks/{symbol}/bars"
    params = {
        "timeframe": timeframe,
        "start": start,
        "limit": min(lookback_bars, 10000),
    }
    
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        
        if "bars" not in data or len(data["bars"]) == 0:
            return pd.DataFrame()
        
        rows = []
        for bar in data["bars"]:
            rows.append({
                "timestamp": pd.Timestamp(bar["t"]),
                "open": float(bar["o"]),
                "high": float(bar["h"]),
                "low": float(bar["l"]),
                "close": float(bar["c"]),
                "volume": int(bar["v"]),
                "symbol": symbol.upper(),
                "interval": interval,
            })
        
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"  [WARN] Alpaca fetch failed for {symbol} {interval}: {e}")
        return pd.DataFrame()


def get_intraday_bars(
    symbol: str,
    interval: str = "5m",
    lookback_bars: int = 500,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Fetch intraday bars for a stock symbol.
    
    Uses Alpaca if API keys are set, otherwise falls back to yfinance.
    
    Args:
        symbol: Stock ticker (e.g. 'AAPL', 'MSFT', 'SPY')
        interval: '1m', '5m', '15m', '30m', '60m', '1h'
        lookback_bars: Number of bars to return
        
    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume, symbol, interval
    """
    symbol = symbol.upper()
    
    # Try cache
    if use_cache and _is_cache_valid(symbol, interval):
        df = pd.read_parquet(_cache_path(symbol, interval))
        if len(df) >= lookback_bars:
            return df.tail(lookback_bars).reset_index(drop=True)
    
    # Fetch from appropriate source
    if USE_ALPACA:
        from alpaca_connector import get_alpaca_bars as _fetch_alpaca_bars
        df = _fetch_alpaca_bars(symbol, interval, lookback_bars)
    else:
        df = _fetch_yfinance(symbol, interval)
    
    if len(df) == 0:
        return df
    
    # Cache
    df.to_parquet(_cache_path(symbol, interval), index=False)
    
    return df.tail(lookback_bars).reset_index(drop=True)


def get_multi_symbol_bars(
    symbols: list,
    interval: str = "5m",
    lookback_bars: int = 500,
) -> dict:
    """Fetch intraday bars for multiple symbols."""
    result = {}
    for sym in symbols:
        df = get_intraday_bars(sym, interval, lookback_bars)
        if len(df) > 0:
            result[sym] = df
    return result


def get_daily_levels(symbol: str) -> dict:
    """
    Get prior day high/low/open/close for sweep level detection.
    
    Returns:
        {'prior_high': float, 'prior_low': float, 'prior_close': float,
         'current_open': float, 'current_high': float, 'current_low': float}
    """
    # Use daily data from yfinance
    import yfinance as yf
    
    try:
        df = yf.download(symbol, period="5d", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        if len(df) < 2:
            return {}
        
        prior = df.iloc[-2]
        current = df.iloc[-1]
        
        return {
            "prior_high": float(prior["High"]),
            "prior_low": float(prior["Low"]),
            "prior_close": float(prior["Close"]),
            "current_open": float(current["Open"]),
            "current_high": float(current["High"]),
            "current_low": float(current["Low"]),
            "prior_date": str(df.index[-2].date()),
            "current_date": str(df.index[-1].date()),
        }
    except Exception as e:
        print(f"  [WARN] get_daily_levels failed for {symbol}: {e}")
        return {}


def get_session_levels(symbol: str, interval: str = "5m") -> dict:
    """
    Get current trading session high/low/open for intraday sweep detection.
    
    For stocks, session = regular trading hours (9:30 AM - 4:00 PM ET).
    
    Returns:
        {'session_open': float, 'session_high': float, 'session_low': float,
         'session_time': str, 'bars': int}
    """
    df = get_intraday_bars(symbol, interval, lookback_bars=100)
    if len(df) == 0:
        return {}
    
    # Filter to today's session (9:30 AM ET = 13:30 UTC)
    today = df["timestamp"].dt.date.iloc[-1]
    session_df = df[df["timestamp"].dt.date == today].copy()
    
    # For stocks, filter to RTH (13:30 UTC to 20:00 UTC)
    if len(session_df) > 0:
        session_utc_hour = session_df["timestamp"].dt.hour
        rth_mask = (session_utc_hour >= 13) & (session_utc_hour < 20)
        rth_df = session_df[rth_mask]
        if len(rth_df) > 0:
            session_df = rth_df
    
    if len(session_df) == 0:
        return {}
    
    return {
        "session_open": float(session_df["open"].iloc[0]),
        "session_high": float(session_df["high"].max()),
        "session_low": float(session_df["low"].min()),
        "session_close": float(session_df["close"].iloc[-1]),
        "session_time": str(session_df["timestamp"].iloc[-1]),
        "bars": len(session_df),
    }


if __name__ == "__main__":
    print(f"Data source: {'Alpaca' if USE_ALPACA else 'yfinance (free)'}")
    print()
    
    print("=== Testing Stock Intraday Data ===\n")
    
    for sym in ["SPY", "AAPL", "NVDA"]:
        for interval in ["5m", "15m"]:
            df = get_intraday_bars(sym, interval, lookback_bars=100)
            if len(df) > 0:
                print(f"{sym} {interval}: {len(df)} bars")
                print(f"  Range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
                print(f"  Last close: ${df['close'].iloc[-1]:.2f}")
                print()
            else:
                print(f"{sym} {interval}: NO DATA")
                print()
    
    print("=== Daily Levels ===")
    levels = get_daily_levels("SPY")
    for k, v in levels.items():
        print(f"  {k}: {v}")
    
    print("\n=== Session Levels ===")
    sl = get_session_levels("SPY", "5m")
    for k, v in sl.items():
        print(f"  {k}: {v}")
