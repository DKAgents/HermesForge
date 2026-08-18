#!/usr/bin/env python3
"""
compute_rotation.py — Sector Rotation + Crypto Performance Heatmap

Computes rolling relative strength of sectors vs SPY and crypto
performance across multiple timeframes. Useful for visual heatmap
output and as strategy input signals.

Usage:
    python3 compute_rotation.py
    python3 compute_rotation.py --json
"""

import sys
import json
import pathlib
import argparse
import pandas as pd
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "paper_trading"))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "validation"))

SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLV": "Healthcare",
    "XLI": "Industrials",
    "XLY": "Consumer Disc.",
    "XLP": "Consumer Stap.",
    "XLU": "Utilities",
    "XLB": "Materials",
    "XLRE": "Real Estate",
    "XLC": "Communications",
}

# --- Universe (single source of truth) ----------------------------------------
import pathlib as _pl
import sys as _sys
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent))
from config.universe import CRYPTO_UNIVERSE  # noqa: E402


def _returns(close: pd.Series, periods: list) -> dict:
    """Compute returns over multiple periods."""
    result = {}
    for p in periods:
        if len(close) > p:
            result[f"{p}d"] = float((close.iloc[-1] / close.iloc[-1 - p] - 1) * 100)
        else:
            result[f"{p}d"] = 0.0
    return result


def compute_sector_rotation() -> dict:
    """
    Compute sector rotation: relative strength of each sector vs SPY.
    
    Returns:
    {
        "SPY": {returns},
        "sectors": {
            "XLK": {"name": "Technology", "returns": {...}, "rs_vs_spy": {...}},
            ...
        },
        "leading_sector": str,
        "lagging_sector": str,
    }
    """
    from fetch_data import load_all
    stock_data = load_all()
    
    periods = [1, 5, 10, 20, 60, 120]
    spy_returns = {}
    if "SPY" in stock_data:
        spy_returns = _returns(stock_data["SPY"]["close"], periods)
    
    sectors = {}
    for etf, name in SECTOR_ETFS.items():
        if etf not in stock_data:
            continue
        rets = _returns(stock_data[etf]["close"], periods)
        
        # Relative strength vs SPY
        rs = {}
        for p in periods:
            key = f"{p}d"
            rs[key] = round(rets.get(key, 0) - spy_returns.get(key, 0), 2)
        
        sectors[etf] = {
            "name": name,
            "returns": {k: round(v, 2) for k, v in rets.items()},
            "rs_vs_spy": rs,
        }
    
    # Leading/lagging by 20-day relative strength
    if sectors:
        rs_20d = {etf: s["rs_vs_spy"].get("20d", 0) for etf, s in sectors.items()}
        leading = max(rs_20d, key=rs_20d.get)
        lagging = min(rs_20d, key=rs_20d.get)
    else:
        leading = lagging = ""
    
    return {
        "SPY": spy_returns,
        "sectors": sectors,
        "leading_sector": f"{leading} ({SECTOR_ETFS.get(leading, '')})" if leading else "",
        "lagging_sector": f"{lagging} ({SECTOR_ETFS.get(lagging, '')})" if lagging else "",
    }


def compute_crypto_heatmap() -> dict:
    """
    Compute crypto performance heatmap across timeframes.
    
    Returns:
    {
        coin: {"1d": x, "7d": x, "30d": x, "90d": x},
        ...
    }
    """
    from fetch_crypto_data import load_all as load_crypto
    crypto_data = load_crypto()
    
    periods = [1, 7, 30, 90]
    heatmap = {}
    
    for coin in CRYPTO_UNIVERSE:
        if coin in crypto_data:
            close = crypto_data[coin]["close"]
            heatmap[coin] = _returns(close, periods)
    
    return heatmap


def get_rotation_summary() -> dict:
    """Get rotation summary for regime filter."""
    rotation = compute_sector_rotation()
    crypto = compute_crypto_heatmap()
    return {
        "leading_sector": rotation.get("leading_sector", ""),
        "lagging_sector": rotation.get("lagging_sector", ""),
        "sectors": {etf: s["rs_vs_spy"]["20d"] for etf, s in rotation.get("sectors", {}).items()},
        "crypto_30d": {coin: data.get("30d", 0) for coin, data in crypto.items()},
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Sector rotation + crypto heatmap")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    
    rotation = compute_sector_rotation()
    crypto = compute_crypto_heatmap()
    
    if args.json:
        print(json.dumps({"sector_rotation": rotation, "crypto_heatmap": crypto}, indent=2, default=str))
    else:
        print("\n📊 **Sector Rotation (Relative Strength vs SPY)**\n")
        print(f"Leading: {rotation['leading_sector']}")
        print(f"Lagging: {rotation['lagging_sector']}")
        print(f"\n{'ETF':<6} {'Sector':<16} {'1d':>8} {'5d':>8} {'20d':>8} {'60d':>8} {'120d':>8}")
        print("-" * 62)
        for etf, data in sorted(rotation["sectors"].items(),
                                 key=lambda x: x[1]["rs_vs_spy"]["20d"], reverse=True):
            rs = data["rs_vs_spy"]
            print(f"{etf:<6} {data['name']:<16} {rs['1d']:>+8.2f} {rs['5d']:>+8.2f} "
                  f"{rs['20d']:>+8.2f} {rs['60d']:>+8.2f} {rs['120d']:>+8.2f}")
        
        print(f"\n📊 **Crypto Performance Heatmap**\n")
        print(f"{'Coin':<8} {'1d':>8} {'7d':>8} {'30d':>8} {'90d':>8}")
        print("-" * 40)
        for coin, rets in sorted(crypto.items(), key=lambda x: x[1].get("30d", 0), reverse=True):
            print(f"{coin:<8} {rets['1d']:>+8.2f} {rets['7d']:>+8.2f} "
                  f"{rets['30d']:>+8.2f} {rets['90d']:>+8.2f}")
