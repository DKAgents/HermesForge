#!/usr/bin/env python3
"""
fetch_fear_greed.py — Crypto Fear & Greed Index (alternative.me)

Free API, no key required. Historical data back to 2018.
URL: https://api.alternative.me/fng/

Caches to ~/.hermes/market_data/fear_greed.parquet
Refreshes if cache > 1 day old.

Usage:
    python3 fetch_fear_greed.py              # fetch/update
    python3 fetch_fear_greed.py --force       # force refresh
    python3 fetch_fear_greed.py --days 30     # last 30 days only
"""

import sys
import time
import json
import pathlib
import argparse
import requests
import pandas as pd
from datetime import datetime, timezone

API_URL = "https://api.alternative.me/fng/"
CACHE_PATH = pathlib.Path.home() / ".hermes" / "market_data" / "fear_greed.parquet"
CACHE_MAX_AGE_HOURS = 12  # F&G updates daily, refresh twice a day


def fetch_fear_greed(days: int = 0) -> pd.DataFrame:
    """
    Fetch Fear & Greed Index data.
    
    Args:
        days: Number of days of history (0 = all available)
    
    Returns:
        DataFrame with columns: date, value (int 0-100), classification (str)
    """
    limit = days if days > 0 else 0  # 0 = all available
    # Note: limit=0 returns ALL available data (~3100 days back to 2018)
    url = f"{API_URL}?limit={limit}"
    if limit == 0:
        url = f"{API_URL}?limit=0"  # explicit 0 = all data per API docs
    
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()["data"]
    
    rows = []
    for item in data:
        rows.append({
            "date": pd.Timestamp(datetime.fromtimestamp(int(item["timestamp"]), tz=timezone.utc).strftime("%Y-%m-%d")),
            "value": int(item["value"]),
            "classification": item["value_classification"],
        })
    
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    return df


def load_fear_greed(force: bool = False, days: int = 0) -> pd.DataFrame:
    """
    Load F&G data from cache or fetch fresh.
    """
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    if not force and CACHE_PATH.exists():
        mtime = datetime.fromtimestamp(CACHE_PATH.stat().st_mtime, tz=timezone.utc)
        age = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600
        if age < CACHE_MAX_AGE_HOURS:
            return pd.read_parquet(CACHE_PATH)
    
    df = fetch_fear_greed(days=days)
    df.to_parquet(CACHE_PATH, index=False)
    print(f"Fear & Greed: {len(df)} days cached to {CACHE_PATH}", file=sys.stderr)
    return df


def get_current_fg() -> dict:
    """Get latest F&G value as a dict."""
    df = load_fear_greed()
    if df.empty:
        return {"value": 50, "classification": "Neutral", "date": ""}
    latest = df.iloc[-1]
    return {
        "value": int(latest["value"]),
        "classification": latest["classification"],
        "date": str(latest["date"].date()),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch Crypto Fear & Greed Index")
    ap.add_argument("--force", action="store_true", help="Force refresh cache")
    ap.add_argument("--days", type=int, default=0, help="Number of days (0=all)")
    args = ap.parse_args()
    
    df = load_fear_greed(force=args.force, days=args.days)
    print(f"\nFear & Greed Index — {len(df)} records")
    print(f"Latest: {df.iloc[-1]['value']} ({df.iloc[-1]['classification']}) on {df.iloc[-1]['date']}")
    print(f"\nLast 7 days:")
    for _, row in df.tail(7).iterrows():
        print(f"  {row['date']} — {row['value']} ({row['classification']})")
