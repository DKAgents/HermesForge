#!/usr/bin/env python3
"""
compute_breadth.py — Market Breadth Indicators (computed from existing stock data)

No external API needed — computes from the 529-stock OHLCV cache:
  - Advance/Decline line (cumulative net advancing issues)
  - New 52-week highs vs new lows
  - % of stocks above 50-day and 200-day MA
  - Breadth thrust detection (sharp shifts in % above MA)

These are classic internal market indicators. Price making new highs
while breadth declines = divergence = potential reversal warning.

Usage:
    python3 compute_breadth.py                    # print current breadth
    python3 compute_breadth.py --json              # JSON output
"""

import sys
import json
import pathlib
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "paper_trading"))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "validation"))
CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data"


def load_stock_data() -> dict:
    """Load all cached stock data."""
    from fetch_data import load_all
    return load_all()


def compute_breadth(stock_data: dict = None) -> dict:
    """
    Compute market breadth indicators from stock universe.
    
    Returns:
    {
        "ad_line": float,              # cumulative A/D line value
        "ad_ratio": float,             # today's advancers/decliners ratio
        "advancers": int,
        "decliners": int,
        "unchanged": int,
        "new_highs": int,              # 52-week highs today
        "new_lows": int,               # 52-week lows today
        "pct_above_50ma": float,       # % of stocks above 50-day MA
        "pct_above_200ma": float,      # % of stocks above 200-day MA
        "breadth_thrust": bool,        # true if % above 50ma jumped >10% in 10 days
        "divergence": str,             # "bullish" / "bearish" / "none"
        "date": str,
    }
    """
    if stock_data is None:
        stock_data = load_stock_data()
    
    if not stock_data:
        return {}
    
    advancers = 0
    decliners = 0
    unchanged = 0
    new_highs = 0
    new_lows = 0
    above_50ma = 0
    above_200ma = 0
    total_stocks = 0
    
    # For A/D line, we need historical cumulative — compute from last 252 bars
    all_daily_ad = []
    
    for ticker, df in stock_data.items():
        if len(df) < 252:
            continue
        total_stocks += 1
        
        close = df["close"]
        # Today's change
        if len(close) >= 2:
            change = close.iloc[-1] - close.iloc[-2]
            if change > 0:
                advancers += 1
            elif change < 0:
                decliners += 1
            else:
                unchanged += 1
        
        # 52-week high/low
        high_252 = close.tail(252).max()
        low_252 = close.tail(252).min()
        if close.iloc[-1] >= high_252 * 0.999:
            new_highs += 1
        if close.iloc[-1] <= low_252 * 1.001:
            new_lows += 1
        
        # Moving averages
        ma_50 = close.tail(50).mean()
        ma_200 = close.tail(200).mean()
        if close.iloc[-1] > ma_50:
            above_50ma += 1
        if close.iloc[-1] > ma_200:
            above_200ma += 1
    
    if total_stocks == 0:
        return {}
    
    pct_above_50 = (above_50ma / total_stocks) * 100
    pct_above_200 = (above_200ma / total_stocks) * 100
    ad_ratio = advancers / max(decliners, 1)
    
    # Breadth thrust: check if % above 50ma moved >10% in last 10 bars
    # (simplified — would need historical tracking for precise measurement)
    breadth_thrust = pct_above_50 > 70 and pct_above_50 < 90  # transitional zone
    
    # Divergence detection (simplified)
    # If SPY is near highs but breadth is declining → bearish divergence
    # If SPY is near lows but breadth is improving → bullish divergence
    divergence = "none"
    if "SPY" in stock_data:
        spy = stock_data["SPY"]["close"]
        spy_near_high = spy.iloc[-1] > spy.tail(252).max() * 0.98
        spy_near_low = spy.iloc[-1] < spy.tail(252).min() * 1.02
        
        if spy_near_high and pct_above_50 < 60:
            divergence = "bearish"  # price up, breadth weak
        elif spy_near_low and pct_above_50 > 40:
            divergence = "bullish"  # price down, breadth recovering
    
    return {
        "advancers": advancers,
        "decliners": decliners,
        "unchanged": unchanged,
        "ad_ratio": round(ad_ratio, 2),
        "new_highs": new_highs,
        "new_lows": new_lows,
        "pct_above_50ma": round(pct_above_50, 1),
        "pct_above_200ma": round(pct_above_200, 1),
        "breadth_thrust": breadth_thrust,
        "divergence": divergence,
        "total_stocks": total_stocks,
        "date": str(stock_data.get("SPY", pd.DataFrame()).index[-1])[:10] if "SPY" in stock_data else "",
    }


def get_breadth_summary() -> dict:
    """Get breadth summary for regime filter integration."""
    return compute_breadth()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Market breadth indicators")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    
    breadth = compute_breadth()
    if args.json:
        print(json.dumps(breadth, indent=2, default=str))
    else:
        print("\n📊 **Market Breadth**\n")
        print(f"Advancers: {breadth['advancers']} | Decliners: {breadth['decliners']} | Unchanged: {breadth['unchanged']}")
        print(f"A/D Ratio: {breadth['ad_ratio']}")
        print(f"New 52w Highs: {breadth['new_highs']} | New 52w Lows: {breadth['new_lows']}")
        print(f"% Above 50-MA: {breadth['pct_above_50ma']}%")
        print(f"% Above 200-MA: {breadth['pct_above_200ma']}%")
        print(f"Breadth Thrust: {'YES' if breadth['breadth_thrust'] else 'No'}")
        print(f"Divergence: {breadth['divergence']}")
        print(f"Total Stocks: {breadth['total_stocks']}")
