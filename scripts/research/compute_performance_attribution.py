#!/usr/bin/env python3
"""
compute_performance_attribution.py — Trade Performance Attribution

Analyzes which regime tags and market conditions actually predict winning
trades. We have 34 trades tagged with VIX, DXY, F&G, regime_stock,
regime_crypto, regime_overall. This module finds which tags correlate
with profitability.

Analysis dimensions:
  1. By regime (stock_regime, crypto_regime, overall)
  2. By VIX level (bins: <15, 15-20, 20-28, >28)
  3. By F&G level (bins: <25, 25-45, 45-55, 55-75, >75)
  4. By DXY trend (up, down, flat)
  5. By strategy
  6. By asset class
  7. By direction (long/short)

For each dimension, compute: trade count, win rate, avg R, total R,
and statistical significance (p-value via t-test).

Usage:
    python3 compute_performance_attribution.py
    python3 compute_performance_attribution.py --json
"""

import sys
import json
import argparse
import pathlib
import pandas as pd
import numpy as np
from datetime import datetime
from statistics import NormalDist

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
TRADES_PATH = REPO_ROOT / "scripts" / "paper_trading" / "trades.csv"


def _t_test(r_values: list) -> dict:
    """One-sample t-test: is mean R significantly different from 0?"""
    if len(r_values) < 3:
        return {"mean": 0, "t_stat": 0, "p_value": 1.0, "significant": False}
    
    r = np.array(r_values, dtype=float)
    mean = float(np.mean(r))
    std = float(np.std(r, ddof=1))
    if std == 0:
        return {"mean": mean, "t_stat": 0, "p_value": 1.0, "significant": False}
    
    n = len(r)
    t_stat = mean / (std / np.sqrt(n))
    # Two-tailed p-value
    p_value = 2 * (1 - NormalDist().cdf(abs(t_stat)))
    
    return {
        "mean": round(mean, 3),
        "t_stat": round(t_stat, 3),
        "p_value": round(p_value, 4),
        "significant": p_value < 0.10,
    }


def _bin_vix(vix: float) -> str:
    if pd.isna(vix) or vix == 0:
        return "unknown"
    if vix < 15:
        return "low (<15)"
    elif vix < 20:
        return "normal (15-20)"
    elif vix < 28:
        return "elevated (20-28)"
    else:
        return "high (>28)"


def _bin_fg(fg) -> str:
    try:
        fg = float(fg)
    except (ValueError, TypeError):
        return "unknown"
    if pd.isna(fg):
        return "unknown"
    if fg < 25:
        return "extreme fear (<25)"
    elif fg < 45:
        return "fear (25-45)"
    elif fg < 55:
        return "neutral (45-55)"
    elif fg < 75:
        return "greed (55-75)"
    else:
        return "extreme greed (>75)"


def _analyze_dimension(df: pd.DataFrame, dim_col: str, label: str) -> dict:
    """Analyze performance by a single dimension."""
    result = {"dimension": label, "column": dim_col, "groups": {}}
    
    if dim_col not in df.columns or df[dim_col].isna().all():
        return result
    
    # Filter to closed trades with R data
    closed = df[df["status"] == "closed"].copy()
    closed["r_multiple"] = pd.to_numeric(closed["r_multiple"], errors="coerce")
    closed = closed[closed["r_multiple"].notna()]
    
    if len(closed) < 3:
        result["note"] = f"Only {len(closed)} closed trades — insufficient"
        return result
    
    for group_val in closed[dim_col].dropna().unique():
        group_trades = closed[closed[dim_col] == group_val]
        r_values = group_trades["r_multiple"].tolist()
        
        if len(r_values) < 1:
            continue
        
        wins = sum(1 for r in r_values if r > 0)
        stats = _t_test(r_values)
        
        result["groups"][str(group_val)] = {
            "count": len(r_values),
            "win_rate": round(wins / len(r_values) * 100, 1),
            "avg_r": stats["mean"],
            "total_r": round(sum(r_values), 2),
            "t_stat": stats["t_stat"],
            "p_value": stats["p_value"],
            "significant": stats["significant"],
        }
    
    # Find best and worst groups
    groups = result["groups"]
    if groups:
        sorted_groups = sorted(groups.items(), key=lambda x: x[1]["avg_r"], reverse=True)
        result["best_group"] = {
            "name": sorted_groups[0][0],
            **sorted_groups[0][1],
        }
        result["worst_group"] = {
            "name": sorted_groups[-1][0],
            **sorted_groups[-1][1],
        }
    
    return result


def run_attribution() -> dict:
    """Run full performance attribution analysis."""
    if not TRADES_PATH.exists():
        return {"error": "No trades.csv found"}
    
    df = pd.read_csv(TRADES_PATH)
    
    # Add VIX bins and F&G bins
    df["vix_bin"] = df["vix"].apply(_bin_vix) if "vix" in df.columns else "unknown"
    df["fg_bin"] = df["fear_greed"].apply(_bin_fg) if "fear_greed" in df.columns else "unknown"
    
    # Run analysis on each dimension
    dimensions = [
        ("regime_stock", "Stock Regime"),
        ("regime_crypto", "Crypto Regime"),
        ("regime_overall", "Overall Regime"),
        ("vix_bin", "VIX Level"),
        ("fg_bin", "Fear & Greed Level"),
        ("dxy", "DXY (raw)"),
        ("strategy_id", "Strategy"),
        ("asset_class", "Asset Class"),
        ("direction", "Direction"),
    ]
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_trades": len(df),
        "closed_trades": len(df[df["status"] == "closed"]),
        "dimensions": {},
    }
    
    for col, label in dimensions:
        results["dimensions"][label] = _analyze_dimension(df, col, label)
    
    # Cross-analysis: VIX bin × direction
    closed = df[df["status"] == "closed"].copy()
    closed["r_multiple"] = pd.to_numeric(closed["r_multiple"], errors="coerce")
    closed = closed[closed["r_multiple"].notna()]
    
    cross = {}
    for vix_b in closed["vix_bin"].unique():
        for direction in closed["direction"].unique():
            subset = closed[(closed["vix_bin"] == vix_b) & (closed["direction"] == direction)]
            if len(subset) >= 3:
                r_vals = subset["r_multiple"].tolist()
                stats = _t_test(r_vals)
                cross[f"{vix_b}/{direction}"] = {
                    "count": len(r_vals),
                    "win_rate": round(sum(1 for r in r_vals if r > 0) / len(r_vals) * 100, 1),
                    "avg_r": stats["mean"],
                    "p_value": stats["p_value"],
                }
    
    if cross:
        results["cross_analysis_vix_direction"] = cross
    
    # Key findings
    findings = []
    for dim_name, dim_data in results["dimensions"].items():
        if dim_data.get("best_group") and dim_data["best_group"].get("count", 0) >= 3:
            bg = dim_data["best_group"]
            if bg["avg_r"] > 0.3 and bg["p_value"] < 0.15:
                findings.append(f"✅ {dim_name}={bg['name']}: WR={bg['win_rate']}%, "
                                f"avg={bg['avg_r']:+.2f}R (n={bg['count']}, p={bg['p_value']:.3f})")
        if dim_data.get("worst_group") and dim_data["worst_group"].get("count", 0) >= 3:
            wg = dim_data["worst_group"]
            if wg["avg_r"] < -0.2:
                findings.append(f"❌ {dim_name}={wg['name']}: WR={wg['win_rate']}%, "
                                f"avg={wg['avg_r']:+.2f}R (n={wg['count']}, p={wg['p_value']:.3f})")
    
    results["key_findings"] = findings
    
    return results


def get_attribution_summary() -> dict:
    """Get concise summary for regime filter / briefing."""
    full = run_attribution()
    if full.get("error"):
        return {"available": False, "note": full["error"]}
    
    return {
        "available": True,
        "total_trades": full.get("total_trades", 0),
        "closed_trades": full.get("closed_trades", 0),
        "key_findings": full.get("key_findings", [])[:5],
        "best_regime": full.get("dimensions", {}).get("Overall Regime", {}).get("best_group", {}),
        "worst_regime": full.get("dimensions", {}).get("Overall Regime", {}).get("worst_group", {}),
    }


def print_report(results: dict):
    print(f"\n📊 **Performance Attribution Report**")
    print(f"   {results.get('timestamp', '')[:19]}")
    print(f"   Total trades: {results.get('total_trades', 0)} | Closed: {results.get('closed_trades', 0)}\n")
    
    for dim_name, dim_data in results.get("dimensions", {}).items():
        print(f"\n**{dim_name}**")
        groups = dim_data.get("groups", {})
        if not groups:
            print(f"  {dim_data.get('note', 'No data')}")
            continue
        
        for group_name, stats in sorted(groups.items(), key=lambda x: x[1]["avg_r"], reverse=True):
            sig = " ★" if stats.get("significant") else ""
            print(f"  {group_name}: n={stats['count']}, WR={stats['win_rate']}%, "
                  f"avg={stats['avg_r']:+.2f}R, total={stats['total_r']:+.2f}R, "
                  f"p={stats['p_value']:.3f}{sig}")
    
    if results.get("key_findings"):
        print(f"\n**Key Findings:**")
        for f in results["key_findings"]:
            print(f"  {f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Performance Attribution")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    
    results = run_attribution()
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print_report(results)
