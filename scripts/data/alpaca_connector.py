#!/usr/bin/env python3
"""
alpaca_connector.py
===================
HermesForge US-107 — Alpaca Markets API connector for extended intraday stock data.

Alpaca's free tier provides:
  - 7+ years of 1-minute bar data
  - 200 API requests/minute
  - No funding required (paper trading account)
  - Full OHLCV + trade count + VWAP

This module is a drop-in upgrade for fetch_intraday_stocks.py.
When ALPACA_API_KEY and ALPACA_API_SECRET are set in .env, 
fetch_intraday_stocks.py automatically uses this connector.

SETUP INSTRUCTIONS:
1. Sign up for a free account at https://alpaca.markets
2. Go to https://app.alpaca.markets/paper/dashboard/overview
3. Click "Your API Keys" in the sidebar
4. Copy the API Key ID and Secret Key
5. Add to ~/.hermes/.env:
   ALPACA_API_KEY=your_key_id_here
   ALPACA_API_SECRET=your_secret_key_here
6. Restart Hermes or re-source the environment

LIMITATIONS (free tier):
  - 200 requests/minute (rate limited)
  - IEX data only (15 min delayed for non-real-time)
  - No options or crypto data from this endpoint
  - Some symbols may have limited history

RATE LIMIT HANDLING:
  - Automatic retry with backoff on 429 responses
  - Request batching (1000 bars per call)
  - Local caching reduces redundant calls

Usage:
  from alpaca_connector import get_alpaca_bars
  df = get_alpaca_bars('AAPL', '5Min', lookback_bars=1000)
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

# ── Configuration ────────────────────────────────────────────────────────────

CACHE_DIR = Path.home() / ".hermes" / "market_data" / "intraday" / "stocks"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Alpaca API endpoints
ALPACA_DATA_URL = "https://data.alpaca.markets/v2"
ALPACA_PAPER_URL = "https://paper-api.alpaca.markets/v2"

# Rate limit: 200 req/min = 1 req per 0.3s minimum
MIN_REQUEST_INTERVAL = 0.35
_last_request_time = 0

# Max bars per API call
MAX_BARS_PER_CALL = 10000


def _get_headers() -> dict:
    """Get Alpaca API headers from environment."""
    api_key = os.environ.get("ALPACA_API_KEY", "")
    api_secret = os.environ.get("ALPACA_API_SECRET", "")
    
    if not api_key or not api_secret:
        raise ValueError(
            "Alpaca API keys not found. Set ALPACA_API_KEY and ALPACA_API_SECRET "
            "in ~/.hermes/.env. Sign up at https://alpaca.markets (free)."
        )
    
    return {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret,
    }


def _rate_limit():
    """Enforce minimum interval between requests."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


def _cache_path(symbol: str, timeframe: str) -> Path:
    return CACHE_DIR / f"{symbol.upper()}_{timeframe}_alpaca.parquet"


def get_alpaca_bars(
    symbol: str,
    timeframe: str = "5Min",
    lookback_bars: int = 1000,
    start: str = None,
    end: str = None,
) -> pd.DataFrame:
    """
    Fetch intraday bars from Alpaca Markets API.
    
    Args:
        symbol: Stock ticker (e.g. 'AAPL', 'SPY')
        timeframe: '1Min', '5Min', '15Min', '30Min', '1Hour'
        lookback_bars: Number of bars to fetch (will paginate if > 10000)
        start: ISO datetime string (optional, overrides lookback_bars)
        end: ISO datetime string (optional, defaults to now)
    
    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume, 
        vwap, trade_count, symbol, interval
    """
    headers = _get_headers()
    
    # Calculate time range
    timeframe_minutes = {
        "1Min": 1, "5Min": 5, "15Min": 15, "30Min": 30, "1Hour": 60,
    }
    mins = timeframe_minutes.get(timeframe, 5)
    
    if end is None:
        end_dt = datetime.now(timezone.utc)
    else:
        end_dt = pd.Timestamp(end).tz_localize("UTC") if pd.Timestamp(end).tz is None else pd.Timestamp(end)
    
    if start is None:
        # Add 20% buffer to ensure we get enough bars
        start_dt = end_dt - timedelta(minutes=int(mins * lookback_bars * 1.2))
    else:
        start_dt = pd.Timestamp(start).tz_localize("UTC") if pd.Timestamp(start).tz is None else pd.Timestamp(start)
    
    all_bars = []
    current_start = start_dt.isoformat()
    current_end = end_dt.isoformat()
    
    bars_remaining = lookback_bars
    
    while bars_remaining > 0:
        _rate_limit()
        
        params = {
            "timeframe": timeframe,
            "start": current_start,
            "end": current_end,
            "limit": min(bars_remaining, MAX_BARS_PER_CALL),
            "adjustment": "raw",
        }
        
        url = f"{ALPACA_DATA_URL}/stocks/{symbol}/bars"
        
        try:
            r = requests.get(url, headers=headers, params=params, timeout=15)
            
            if r.status_code == 429:
                # Rate limited — back off
                retry_after = int(r.headers.get("Retry-After", "5"))
                print(f"  [Alpaca] Rate limited, waiting {retry_after}s...")
                time.sleep(retry_after)
                continue
            
            r.raise_for_status()
            data = r.json()
            
            bars = data.get("bars", [])
            if not bars:
                break
            
            all_bars.extend(bars)
            bars_remaining -= len(bars)
            
            # Move window back
            last_bar_time = pd.Timestamp(bars[0]["t"])
            current_end = last_bar_time.isoformat()
            
            if len(bars) < MAX_BARS_PER_CALL:
                break  # no more data
                
        except requests.exceptions.HTTPError as e:
            if r.status_code == 403:
                print(f"  [Alpaca] Authentication failed — check API keys in .env")
            elif r.status_code == 422:
                print(f"  [Alpaca] Symbol {symbol} not available")
            else:
                print(f"  [Alpaca] HTTP error {r.status_code}: {e}")
            break
        except Exception as e:
            print(f"  [Alpaca] Error fetching {symbol}: {e}")
            break
    
    if not all_bars:
        return pd.DataFrame()
    
    # Convert to DataFrame
    rows = []
    for bar in all_bars:
        rows.append({
            "timestamp": pd.Timestamp(bar["t"]),
            "open": float(bar["o"]),
            "high": float(bar["h"]),
            "low": float(bar["l"]),
            "close": float(bar["c"]),
            "volume": int(bar["v"]),
            "vwap": float(bar.get("vw", 0)),
            "trade_count": int(bar.get("n", 0)),
            "symbol": symbol.upper(),
            "interval": timeframe,
        })
    
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    
    # Cache
    df.to_parquet(_cache_path(symbol, timeframe), index=False)
    
    return df.tail(lookback_bars).reset_index(drop=True)


def get_alpaca_daily_levels(symbol: str) -> dict:
    """Get prior day high/low/open/close from Alpaca daily bars."""
    df = get_alpaca_bars(symbol, "1Hour", lookback_bars=48)
    if len(df) < 10:
        return {}
    
    # Aggregate hourly to daily
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


def test_connection() -> bool:
    """Test Alpaca API connection."""
    try:
        headers = _get_headers()
        r = requests.get(f"{ALPACA_PAPER_URL}/account", headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            print(f"  Connected to Alpaca (account: {data.get('account_number', '?')})")
            print(f"  Status: {data.get('status', '?')}")
            print(f"  Buying power: ${float(data.get('buying_power', 0)):,.2f}")
            return True
        else:
            print(f"  Connection failed: HTTP {r.status_code}")
            return False
    except ValueError as e:
        print(f"  {e}")
        return False
    except Exception as e:
        print(f"  Connection error: {e}")
        return False


if __name__ == "__main__":
    print("=== Alpaca Connector Test ===\n")
    
    # Test connection
    if not test_connection():
        print("\n⚠️  Alpaca keys not configured.")
        print("\nSetup instructions:")
        print("1. Sign up free at https://alpaca.markets")
        print("2. Go to https://app.alpaca.markets/paper/dashboard/overview")
        print("3. Click 'Your API Keys' in the sidebar")
        print("4. Copy the API Key ID and Secret Key")
        print("5. Add to ~/.hermes/.env:")
        print("   ALPACA_API_KEY=your_key_id_here")
        print("   ALPACA_API_SECRET=your_secret_key_here")
        print("6. Restart Hermes or re-source the environment")
        sys.exit(1)
    
    # Test data fetch
    print("\n── Testing 5m bars ──")
    for sym in ["SPY", "AAPL", "NVDA"]:
        df = get_alpaca_bars(sym, "5Min", lookback_bars=100)
        if len(df) > 0:
            print(f"  {sym}: {len(df)} bars, range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
        else:
            print(f"  {sym}: NO DATA")
    
    print("\n── Testing 1m bars (7 years back) ──")
    df = get_alpaca_bars("AAPL", "1Min", lookback_bars=1000)
    if len(df) > 0:
        print(f"  AAPL 1m: {len(df)} bars, range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")