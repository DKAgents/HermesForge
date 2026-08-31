#!/usr/bin/env python3
"""
intraday_provider.py — HermesForge Unified Intraday Data Provider

Single entry point for all intraday candle data, with unified Parquet caching.
Routes to Hyperliquid (crypto), yfinance (stocks, free), or Alpaca (stocks, paid)
based on asset_class and available API keys.

Cache format: {TICKER}_{INTERVAL}_{SOURCE}.parquet under ~/.hermes/market_data/

Usage:
    from intraday_provider import IntradayProvider

    provider = IntradayProvider()
    df = provider.get_candles('BTC', '5m', lookback_bars=260)
    # Returns DataFrame with columns: timestamp, open, high, low, close, volume
"""

import os
import json
import time
import pathlib
import pandas as pd
from typing import Optional
from datetime import datetime, timezone

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data"
CACHE_TTL_SECONDS = 300  # 5 minutes — matches cron polling interval


class IntradayProvider:
    """Unified intraday data provider with Parquet caching."""

    def __init__(self, cache_dir: pathlib.Path = CACHE_DIR,
                 cache_ttl: int = CACHE_TTL_SECONDS):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = cache_ttl

    def get_candles(self, ticker: str, interval: str = "5m",
                    asset_class: str = "crypto", lookback_bars: int = 260) -> Optional[pd.DataFrame]:
        """Get intraday candles for a ticker. Returns DataFrame or None on failure."""
        source = self._resolve_source(asset_class)
        cache_path = self._cache_path(ticker, interval, source)

        # Check cache
        df = self._load_cache(cache_path, lookback_bars)
        if df is not None:
            return df

        # Fetch fresh
        if source == "hyperliquid":
            df = self._fetch_hyperliquid(ticker, interval, lookback_bars)
        elif source == "alpaca":
            df = self._fetch_alpaca(ticker, interval, lookback_bars)
        elif source == "yfinance":
            df = self._fetch_yfinance(ticker, interval, lookback_bars)
        else:
            return None

        # Write cache
        if df is not None and not df.empty:
            self._write_cache(cache_path, df)

        return df

    def _resolve_source(self, asset_class: str) -> str:
        if asset_class == "crypto":
            return "hyperliquid"
        # Alpaca if both key and secret are set, else yfinance
        if os.environ.get("ALPACA_API_KEY") and os.environ.get("ALPACA_API_SECRET"):
            return "alpaca"
        return "yfinance"

    def _cache_path(self, ticker: str, interval: str, source: str) -> pathlib.Path:
        return self.cache_dir / f"{ticker}_{interval}_{source}.parquet"

    def _load_cache(self, path: pathlib.Path, lookback_bars: int) -> Optional[pd.DataFrame]:
        if not path.exists():
            return None
        # Check TTL
        age = time.time() - path.stat().st_mtime
        if age > self.cache_ttl:
            return None
        try:
            df = pd.read_parquet(path)
            if len(df) >= lookback_bars:
                return df.tail(lookback_bars)
        except Exception:
            pass
        return None

    def _write_cache(self, path: pathlib.Path, df: pd.DataFrame):
        try:
            df.to_parquet(path, index=False)
        except Exception:
            pass

    def _fetch_hyperliquid(self, ticker: str, interval: str,
                           lookback_bars: int) -> Optional[pd.DataFrame]:
        """Fetch from Hyperliquid API (free, unlimited, no key)."""
        import requests
        interval_map = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                        "1h": "1h", "4h": "4h"}
        hl_interval = interval_map.get(interval, "5m")

        # Lookback in ms: each bar is interval minutes
        bar_minutes = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240}
        mins = bar_minutes.get(interval, 5)
        end_time = int(time.time() * 1000)
        start_time = end_time - (lookback_bars + 50) * mins * 60 * 1000

        url = "https://api.hyperliquid.xyz/info"
        payload = {
            "type": "candleSnapshot",
            "req": {
                "coin": ticker,
                "interval": hl_interval,
                "startTime": start_time,
                "endTime": end_time,
            }
        }

        try:
            resp = requests.post(url, json=payload, timeout=15)
            data = resp.json()
            candles = data if isinstance(data, list) else []
            if not candles:
                return None

            rows = []
            for c in candles:
                rows.append({
                    "timestamp": pd.to_datetime(c["t"], unit="ms", utc=True),
                    "open": float(c["o"]),
                    "high": float(c["h"]),
                    "low": float(c["l"]),
                    "close": float(c["c"]),
                    "volume": float(c["v"]),
                })

            df = pd.DataFrame(rows)
            df = df.sort_values("timestamp").drop_duplicates(subset="timestamp")
            return df.tail(lookback_bars)
        except Exception:
            return None

    def _fetch_yfinance(self, ticker: str, interval: str,
                        lookback_bars: int) -> Optional[pd.DataFrame]:
        """Fetch from yfinance (free, rate-limited)."""
        try:
            import yfinance as yf

            interval_map = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                            "1h": "60m", "4h": "1h"}  # yfinance doesn't have 4h
            yf_interval = interval_map.get(interval, "5m")

            # Period mapping
            bar_minutes = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 60}
            mins = bar_minutes.get(interval, 5)
            days_needed = max(7, (lookback_bars * mins) / (24 * 60) * 1.5)
            period = f"{int(days_needed)}d"

            tick = yf.Ticker(ticker)
            df = tick.history(interval=yf_interval, period=period)

            if df is None or df.empty:
                return None

            # Normalize columns
            df = df.reset_index()
            df = df.rename(columns={
                "Datetime": "timestamp", "Open": "open", "High": "high",
                "Low": "low", "Close": "close", "Volume": "volume",
            })

            # Ensure UTC
            if df["timestamp"].dt.tz is None:
                df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
            else:
                df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")

            cols = ["timestamp", "open", "high", "low", "close", "volume"]
            df = df[[c for c in cols if c in df.columns]]
            return df.tail(lookback_bars)
        except Exception:
            return None

    def _fetch_alpaca(self, ticker: str, interval: str,
                      lookback_bars: int) -> Optional[pd.DataFrame]:
        """Fetch from Alpaca (requires ALPACA_API_KEY + ALPACA_API_SECRET)."""
        import requests

        api_key = os.environ.get("ALPACA_API_KEY", "")
        api_secret = os.environ.get("ALPACA_API_SECRET", "")
        if not api_key or not api_secret:
            return None

        headers = {"APCA-API-KEY-ID": api_key, "APCA-API-SECRET-KEY": api_secret}
        timeframe_map = {
            "1m": "1Min", "5m": "5Min", "15m": "15Min",
            "30m": "30Min", "1h": "1Hour",
        }
        timeframe = timeframe_map.get(interval, "5Min")
        interval_minutes = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60}
        mins = interval_minutes.get(interval, 5)

        from datetime import timedelta
        start = (datetime.now(timezone.utc) - timedelta(minutes=mins * lookback_bars * 1.2)).strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            r = requests.get(
                f"https://data.alpaca.markets/v2/stocks/{ticker}/bars",
                headers=headers,
                params={"timeframe": timeframe, "start": start, "limit": min(lookback_bars, 10000)},
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()

            if "bars" not in data or not data["bars"]:
                return None

            rows = []
            for bar in data["bars"]:
                rows.append({
                    "timestamp": pd.Timestamp(bar["t"], tz="UTC"),
                    "open": float(bar["o"]),
                    "high": float(bar["h"]),
                    "low": float(bar["l"]),
                    "close": float(bar["c"]),
                    "volume": int(bar["v"]),
                })

            df = pd.DataFrame(rows)
            if df.empty:
                return None
            df = df.sort_values("timestamp").drop_duplicates(subset="timestamp")
            return df.tail(lookback_bars)
        except Exception:
            return None


# Singleton for module-level use
_provider: Optional[IntradayProvider] = None


def get_provider() -> IntradayProvider:
    global _provider
    if _provider is None:
        _provider = IntradayProvider()
    return _provider


def get_intraday_candles(ticker: str, interval: str = "5m",
                         asset_class: str = "crypto",
                         lookback_bars: int = 260) -> Optional[pd.DataFrame]:
    """Convenience function — same signature as old fetch_intraday_*.py.
    Returns DataFrame or None."""
    return get_provider().get_candles(ticker, interval, asset_class, lookback_bars)