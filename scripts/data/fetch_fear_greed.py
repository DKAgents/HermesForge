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
MAX_STALENESS_HOURS = 48   # US-128: data older than this → fail-closed in regime logic


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


def check_freshness() -> dict:
    """US-128: Check F&G feed freshness. Returns staleness status + data.

    If the cached data's latest entry is older than MAX_STALENESS_HOURS,
    returns fresh=False and conservative defaults.
    
    Writes fear_greed_last_ok to data-manifest.md on success.
    """
    result = {
        "fresh": False,
        "value": 50,
        "classification": "Neutral",
        "date": "",
        "hours_since_last": 0,
        "error": None,
    }
    if not CACHE_PATH.exists():
        result["error"] = "parquet cache not found"
        return result

    try:
        df = pd.read_parquet(CACHE_PATH)
    except Exception as e:
        result["error"] = f"parquet read error: {e}"
        return result

    if df.empty:
        result["error"] = "parquet is empty"
        return result

    # Find latest date
    date_col = "date" if "date" in df.columns else df.columns[0]
    try:
        df_sorted = df.sort_values(date_col)
        latest_date = pd.Timestamp(df_sorted[date_col].iloc[-1])
    except Exception as e:
        result["error"] = f"date parsing error: {e}"
        return result

    now = pd.Timestamp.now(tz=None)
    age_hours = (now - latest_date).total_seconds() / 3600.0
    result["hours_since_last"] = round(age_hours, 1)
    result["date"] = str(latest_date.date())

    if age_hours <= MAX_STALENESS_HOURS:
        result["fresh"] = True
        val_col = "value" if "value" in df.columns else df.columns[1]
        val = int(df_sorted[val_col].iloc[-1])
        result["value"] = val
        cls_col = "classification" if "classification" in df.columns else None
        if cls_col:
            result["classification"] = str(df_sorted[cls_col].iloc[-1])
        # Update manifest
        _update_manifest(True, result["date"], val, result["classification"])
    else:
        result["fresh"] = False
        # Still read the latest values for reporting, but flag as stale
        val_col = "value" if "value" in df.columns else df.columns[1]
        result["value"] = int(df_sorted[val_col].iloc[-1])
        cls_col = "classification" if "classification" in df.columns else None
        if cls_col:
            result["classification"] = str(df_sorted[cls_col].iloc[-1]) + " (STALE)"
        _update_manifest(False, result["date"], result["value"], result["classification"])

    return result


def _update_manifest(fresh: bool, date: str, value: int, classification: str) -> None:
    """US-128: Update data-manifest.md with F&G freshness."""
    try:
        manifest_path = pathlib.Path("/root/HermesForge/reports/campaigns/2026-09-aegis-rebuild/data-manifest.md")
        if not manifest_path.exists():
            return
        lines = manifest_path.read_text().splitlines()
        with open(manifest_path, "w") as f:
            for line in lines:
                if line.strip().startswith("fear_greed_last_ok:"):
                    status = date if fresh else f"STALE (last: {date}, value: {value})"
                    f.write(f"fear_greed_last_ok: {status}\n")
                elif line.strip().startswith("fear_greed_last_value:"):
                    f.write(f"fear_greed_last_value: {value} ({classification})\n")
                else:
                    f.write(line + "\n")
            if not any("fear_greed_last_ok:" in l for l in lines):
                f.write(f"fear_greed_last_ok: {date}\n")
            if not any("fear_greed_last_value:" in l for l in lines):
                f.write(f"fear_greed_last_value: {value} ({classification})\n")
    except Exception:
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch Crypto Fear & Greed Index")
    ap.add_argument("--force", action="store_true", help="Force refresh cache")
    ap.add_argument("--days", type=int, default=0, help="Number of days (0=all)")
    ap.add_argument("--check", action="store_true", help="US-128: check freshness only, no fetch")
    args = ap.parse_args()
    
    if args.check:
        import json
        result = check_freshness()
        print(json.dumps(result, indent=2))
        if not result["fresh"]:
            sys.exit(1)  # Non-zero exit = stale, triggers alert from no-agent cron
        sys.exit(0)
    
    df = load_fear_greed(force=args.force, days=args.days)
    print(f"\nFear & Greed Index — {len(df)} records")
    print(f"Latest: {df.iloc[-1]['value']} ({df.iloc[-1]['classification']}) on {df.iloc[-1]['date']}")
    print(f"\nLast 7 days:")
    for _, row in df.tail(7).iterrows():
        print(f"  {row['date']} — {row['value']} ({row['classification']})")
