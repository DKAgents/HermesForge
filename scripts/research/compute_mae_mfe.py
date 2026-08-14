#!/usr/bin/env python3
"""
compute_mae_mfe.py — Maximum Adverse/Favorable Excursion Analysis

Analyzes how far trades go against us (MAE) and in our favor (MFE)
before exit. This reveals:
  - Are stops too tight? (high win rate but small wins, big losses when stopped)
  - Are stops too loose? (small losses but they happen often)
  - Could we trail stops for bigger wins? (high MFE but small realized R)
  - Optimal stop placement per strategy

For each closed trade, we compute:
  - MAE: max adverse excursion (lowest point for longs / highest for shorts)
        as a fraction of the initial risk (R)
  - MFE: max favorable excursion (highest point for longs / lowest for shorts)
        as a fraction of initial risk (R)
  - Was the stop hit exactly or with slippage?
  - Could a tighter stop have improved overall R?
  - Could a trailing stop have captured more profit?

Usage:
    python3 compute_mae_mfe.py
    python3 compute_mae_mfe.py --json
"""

import sys
import json
import argparse
import pathlib
import pandas as pd
import numpy as np
from datetime import datetime

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
TRADES_PATH = REPO_ROOT / "scripts" / "paper_trading" / "trades.csv"

sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))


def _compute_excursion(trade: dict, price_data: pd.DataFrame) -> dict:
    """
    Compute MAE and MFE for a single trade.
    
    MAE = max distance price went against entry (in R)
    MFE = max distance price went in favor of entry (in R)
    """
    entry_price = float(trade.get("entry_price", 0))
    stop_price = float(trade.get("stop_price", 0))
    entry_date = trade.get("entry_date", "")
    exit_date = trade.get("exit_date", "")
    direction = trade.get("direction", "long")
    r_multiple = float(trade.get("r_multiple", 0))
    
    if not entry_price or not stop_price or not entry_date:
        return {"mae_r": None, "mfe_r": None, "note": "missing entry/stop/date"}
    
    risk_per_unit = abs(entry_price - stop_price)
    if risk_per_unit == 0:
        return {"mae_r": None, "mfe_r": None, "note": "zero risk (entry=stop)"}
    
    # Slice price data from entry to exit
    price_data.index = pd.to_datetime(price_data.index)
    
    try:
        entry_dt = pd.to_datetime(entry_date)
        if exit_date and exit_date.strip():
            exit_dt = pd.to_datetime(exit_date)
        else:
            exit_dt = price_data.index[-1]
    except Exception:
        return {"mae_r": None, "mfe_r": None, "note": "date parse error"}
    
    # Get bars between entry and exit
    mask = (price_data.index >= entry_dt) & (price_data.index <= exit_dt)
    bars = price_data[mask]
    
    if len(bars) < 2:
        return {"mae_r": None, "mfe_r": None, "note": f"only {len(bars)} bars"}
    
    highs = bars["high"].values if "high" in bars.columns else bars["close"].values
    lows = bars["low"].values if "low" in bars.columns else bars["close"].values
    
    if direction == "long":
        # MAE = how far below entry (worst low)
        adverse = entry_price - np.min(lows)
        # MFE = how far above entry (best high)
        favorable = np.max(highs) - entry_price
    else:  # short
        # MAE = how far above entry (worst high)
        adverse = np.max(highs) - entry_price
        # MFE = how far below entry (best low)
        favorable = entry_price - np.min(lows)
    
    mae_r = adverse / risk_per_unit
    mfe_r = favorable / risk_per_unit
    
    return {
        "mae_r": round(mae_r, 2),
        "mfe_r": round(mfe_r, 2),
        "bars_in_trade": len(bars),
    }


def compute_excursion_analysis() -> dict:
    """Compute MAE/MFE for all closed trades."""
    if not TRADES_PATH.exists():
        return {"error": "No trades.csv found"}
    
    df = pd.read_csv(TRADES_PATH)
    closed = df[df["status"] == "closed"].copy()
    
    if len(closed) < 3:
        return {"error": f"Only {len(closed)} closed trades"}
    
    # Load price data
    from fetch_data import load_all as load_stocks
    from fetch_crypto_data import load_all as load_crypto
    
    print("Loading price data...", file=sys.stderr)
    stock_data = load_stocks()
    crypto_data = load_crypto()
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_closed": len(closed),
        "trades_analyzed": 0,
        "trades": [],
        "by_strategy": {},
    }
    
    for idx, trade in closed.iterrows():
        ticker = trade["ticker"]
        asset_class = trade.get("asset_class", "stock")
        strategy_id = trade.get("strategy_id", "unknown")
        
        # Get price data for this ticker
        if asset_class == "crypto":
            price_df = crypto_data.get(ticker)
        else:
            price_df = stock_data.get(ticker)
        
        if price_df is None:
            continue
        
        exc = _compute_excursion(trade, price_df.copy())
        if exc.get("mae_r") is None:
            continue
        
        trade_result = {
            "ticker": ticker,
            "strategy_id": strategy_id,
            "direction": trade.get("direction", "long"),
            "r_multiple": float(trade.get("r_multiple", 0)),
            "mae_r": exc["mae_r"],
            "mfe_r": exc["mfe_r"],
            "bars_in_trade": exc.get("bars_in_trade", 0),
        }
        results["trades"].append(trade_result)
        results["trades_analyzed"] += 1
        
        # Aggregate by strategy
        if strategy_id not in results["by_strategy"]:
            results["by_strategy"][strategy_id] = {
                "trades": [],
                "avg_mae": [],
                "avg_mfe": [],
                "r_values": [],
            }
        results["by_strategy"][strategy_id]["trades"].append(trade_result)
        results["by_strategy"][strategy_id]["avg_mae"].append(exc["mae_r"])
        results["by_strategy"][strategy_id]["avg_mfe"].append(exc["mfe_r"])
        results["by_strategy"][strategy_id]["r_values"].append(float(trade.get("r_multiple", 0)))
    
    # Compute strategy-level stats
    for strat, data in results["by_strategy"].items():
        maes = data["avg_mae"]
        mfes = data["avg_mfe"]
        rs = data["r_values"]
        
        # Stop too tight? (MAE > 1R frequently means stop was hit)
        stops_hit = sum(1 for m in maes if m >= 1.0)
        
        # Could trail? (MFE > 2R but realized R < 1R means we left money on table)
        left_money = sum(1 for m, r in zip(mfes, rs) if m > 2 and r < 1)
        
        data["stats"] = {
            "count": len(maes),
            "avg_mae_r": round(np.mean(maes), 2),
            "avg_mfe_r": round(np.mean(mfes), 2),
            "max_mae_r": round(max(maes), 2),
            "max_mfe_r": round(max(mfes), 2),
            "stops_hit_pct": round(stops_hit / len(maes) * 100, 1),
            "trailing_opportunity_pct": round(left_money / len(mfes) * 100, 1),
            "avg_realized_r": round(np.mean(rs), 3),
            "mfe_to_realized_ratio": round(np.mean(mfes) / max(abs(np.mean(rs)), 0.01), 2),
        }
        
        # Recommendations
        recs = []
        if data["stats"]["stops_hit_pct"] > 60:
            recs.append(f"⚠️ {data['stats']['stops_hit_pct']:.0f}% of stops hit — consider widening stops")
        if data["stats"]["trailing_opportunity_pct"] > 40:
            recs.append(f"💡 {data['stats']['trailing_opportunity_pct']:.0f}% of trades had MFE > 2R but realized < 1R — add trailing stop")
        if data["stats"]["avg_mae_r"] < 0.5 and data["stats"]["avg_realized_r"] < 0:
            recs.append("🔍 Low MAE but negative R — entry timing may be the issue, not stops")
        data["recommendations"] = recs
    
    # Overall stats
    all_maes = [t["mae_r"] for t in results["trades"]]
    all_mfes = [t["mfe_r"] for t in results["trades"]]
    all_rs = [t["r_multiple"] for t in results["trades"]]
    
    results["overall"] = {
        "avg_mae_r": round(np.mean(all_maes), 2),
        "avg_mfe_r": round(np.mean(all_mfes), 2),
        "stops_hit_pct": round(sum(1 for m in all_maes if m >= 1.0) / len(all_maes) * 100, 1),
        "trailing_opportunity_pct": round(sum(1 for m, r in zip(all_mfes, all_rs) if m > 2 and r < 1) / len(all_mfes) * 100, 1),
        "avg_realized_r": round(np.mean(all_rs), 3),
    }
    
    return results


def get_mae_mfe_summary() -> dict:
    """Get concise summary for regime filter."""
    full = compute_excursion_analysis()
    if full.get("error"):
        return {"available": False, "note": full["error"]}
    
    return {
        "available": True,
        "trades_analyzed": full.get("trades_analyzed", 0),
        "avg_mae_r": full.get("overall", {}).get("avg_mae_r", 0),
        "avg_mfe_r": full.get("overall", {}).get("avg_mfe_r", 0),
        "stops_hit_pct": full.get("overall", {}).get("stops_hit_pct", 0),
        "trailing_opportunity_pct": full.get("overall", {}).get("trailing_opportunity_pct", 0),
    }


def print_report(results: dict):
    if results.get("error"):
        print(f"\n❌ {results['error']}")
        return
    
    print(f"\n📊 **MAE/MFE Excursion Analysis**")
    print(f"   {results['timestamp'][:19]}")
    print(f"   Trades analyzed: {results['trades_analyzed']}/{results['total_closed']}\n")
    
    o = results.get("overall", {})
    print(f"**Overall:**")
    print(f"  Avg MAE: {o.get('avg_mae_r', 0):.2f}R (how far against us)")
    print(f"  Avg MFE: {o.get('avg_mfe_r', 0):.2f}R (how far in our favor)")
    print(f"  Stops hit: {o.get('stops_hit_pct', 0):.1f}% of trades")
    print(f"  Trailing opportunity: {o.get('trailing_opportunity_pct', 0):.1f}% of trades (MFE > 2R but realized < 1R)")
    print(f"  Avg realized R: {o.get('avg_realized_r', 0):+.3f}R")
    print()
    
    print(f"**Per-Strategy:**")
    for strat, data in sorted(results.get("by_strategy", {}).items()):
        s = data.get("stats", {})
        print(f"\n  {strat}:")
        print(f"    Trades: {s.get('count', 0)}")
        print(f"    MAE: avg={s.get('avg_mae_r', 0):.2f}R, max={s.get('max_mae_r', 0):.2f}R")
        print(f"    MFE: avg={s.get('avg_mfe_r', 0):.2f}R, max={s.get('max_mfe_r', 0):.2f}R")
        print(f"    Stops hit: {s.get('stops_hit_pct', 0):.1f}%")
        print(f"    Trailing opportunity: {s.get('trailing_opportunity_pct', 0):.1f}%")
        print(f"    MFE/realized ratio: {s.get('mfe_to_realized_ratio', 0):.2f}")
        for rec in data.get("recommendations", []):
            print(f"    {rec}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="MAE/MFE Excursion Analysis")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    
    results = compute_excursion_analysis()
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print_report(results)
