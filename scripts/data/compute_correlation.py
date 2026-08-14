#!/usr/bin/env python3
"""
compute_correlation.py — Cross-Asset Correlation Matrix

Computes rolling 30-day and 90-day correlations between major assets
and sectors. High correlations = diversification breaks down (risk-off).
Low correlations = stock-picking environment.

Also computes strategy-return correlations for the performance heatmap.

Usage:
    python3 compute_correlation.py
    python3 compute_correlation.py --json
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

KEY_ASSETS = ["SPY", "QQQ", "IWM", "TLT", "GLD", "XLK", "XLF", "XLE", "XLV", "XLI"]


def compute_asset_correlations(window: int = 30) -> dict:
    """
    Compute rolling correlation matrix between key assets.
    
    Returns:
    {
        "window": int,
        "correlations": {asset: {asset: float}},
        "avg_correlation": float,
        "regime": str,  # "diversified" / "normal" / "unified"
    }
    """
    from fetch_data import load_all
    stock_data = load_all()
    
    # Extract close prices for key assets
    closes = {}
    for ticker in KEY_ASSETS:
        if ticker in stock_data:
            closes[ticker] = stock_data[ticker]["close"]
    
    if len(closes) < 3:
        return {"window": window, "correlations": {}, "avg_correlation": 0, "regime": "unknown"}
    
    df = pd.DataFrame(closes)
    returns = df.pct_change().dropna()
    
    # Rolling correlation (last `window` bars)
    if len(returns) < window:
        corr = returns.corr()
    else:
        corr = returns.tail(window).corr()
    
    # Average off-diagonal correlation
    upper_tri = corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1))
    avg_corr = float(upper_tri.stack().mean())
    
    if avg_corr > 0.7:
        regime = "unified"       # everything moving together (risk-off)
    elif avg_corr < 0.3:
        regime = "diversified"   # stock-picking environment
    else:
        regime = "normal"
    
    # Convert to dict
    corr_dict = {}
    for col in corr.columns:
        corr_dict[col] = {}
        for idx in corr.index:
            corr_dict[col][idx] = round(float(corr.loc[idx, col]), 3)
    
    return {
        "window": window,
        "correlations": corr_dict,
        "avg_correlation": round(avg_corr, 3),
        "regime": regime,
    }


def compute_strategy_correlations() -> dict:
    """
    Compute correlations between strategy returns from trades.csv.
    
    Returns:
    {
        "strategy_pairs": {"STR-A/STR-B": float},
        "avg_correlation": float,
    }
    """
    REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
    trades_path = REPO_ROOT / "scripts" / "paper_trading" / "trades.csv"
    
    if not trades_path.exists():
        return {"strategy_pairs": {}, "avg_correlation": 0}
    
    df = pd.read_csv(trades_path)
    closed = df[df["status"] == "closed"].copy()
    
    if len(closed) < 5:
        return {"strategy_pairs": {}, "avg_correlation": 0, "note": "too few closed trades"}
    
    # Group by strategy and date, compute daily R
    closed["exit_date"] = pd.to_datetime(closed["exit_date"], errors="coerce")
    closed["r_multiple"] = pd.to_numeric(closed["r_multiple"], errors="coerce")
    
    strategies = closed["strategy_id"].unique()
    if len(strategies) < 2:
        return {"strategy_pairs": {}, "avg_correlation": 0, "note": "only one strategy"}
    
    # Build daily R series per strategy
    daily_r = {}
    for strat in strategies:
        strat_trades = closed[closed["strategy_id"] == strat]
        daily = strat_trades.groupby(strat_trades["exit_date"].dt.date)["r_multiple"].sum()
        daily_r[strat] = daily
    
    r_df = pd.DataFrame(daily_r).fillna(0)
    corr = r_df.corr()
    
    strategy_pairs = {}
    corrs = []
    for i in range(len(strategies)):
        for j in range(i + 1, len(strategies)):
            s1, s2 = strategies[i], strategies[j]
            if s1 in corr.index and s2 in corr.columns:
                val = float(corr.loc[s1, s2])
                strategy_pairs[f"{s1}/{s2}"] = round(val, 3)
                corrs.append(val)
    
    avg = sum(corrs) / len(corrs) if corrs else 0
    
    return {
        "strategy_pairs": strategy_pairs,
        "avg_correlation": round(avg, 3),
    }


def get_correlation_summary() -> dict:
    """Get correlation summary for regime filter."""
    asset_corr = compute_asset_correlations(30)
    return {
        "avg_asset_correlation": asset_corr.get("avg_correlation", 0),
        "correlation_regime": asset_corr.get("regime", "unknown"),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Cross-asset correlation matrix")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    
    asset_corr = compute_asset_correlations(30)
    strat_corr = compute_strategy_correlations()
    
    if args.json:
        print(json.dumps({
            "asset_correlations": asset_corr,
            "strategy_correlations": strat_corr,
        }, indent=2, default=str))
    else:
        print(f"\n📊 **Cross-Asset Correlations (30-day)**\n")
        print(f"Avg Correlation: {asset_corr['avg_correlation']}")
        print(f"Regime: {asset_corr['regime']}")
        
        # Print matrix
        corrs = asset_corr["correlations"]
        assets = list(corrs.keys())
        if assets:
            print(f"\n{'':<8}", end="")
            for a in assets:
                print(f"{a:>8}", end="")
            print()
            for a1 in assets:
                print(f"{a1:<8}", end="")
                for a2 in assets:
                    val = corrs[a1].get(a2, 0)
                    print(f"{val:>8.2f}", end="")
                print()
        
        print(f"\n📊 **Strategy Return Correlations**\n")
        if strat_corr.get("strategy_pairs"):
            for pair, val in strat_corr["strategy_pairs"].items():
                print(f"  {pair}: {val:+.3f}")
            print(f"\nAvg: {strat_corr['avg_correlation']:+.3f}")
        else:
            print(f"  {strat_corr.get('note', 'No data')}")
