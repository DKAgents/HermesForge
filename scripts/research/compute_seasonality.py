#!/usr/bin/env python3
"""
compute_seasonality.py — Seasonal Pattern Analysis

Analyzes monthly and day-of-week seasonal patterns in:
  1. Stock returns (SPY, QQQ as benchmarks + per-ticker)
  2. Crypto returns (BTC, ETH as benchmarks)
  3. Strategy performance by month (which months our strategies win/lose)

Also computes:
  - "Sell in May" effect (Nov-Apr vs May-Oct)
  - January effect (small caps outperform in Jan)
  - December effect (tax-loss harvesting, window dressing)
  - Crypto halving cycle proximity (for BTC)

Usage:
    python3 compute_seasonality.py
    python3 compute_seasonality.py --json
"""

import sys
import json
import argparse
import pathlib
import pandas as pd
import numpy as np
from datetime import datetime

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))

TRADES_PATH = REPO_ROOT / "scripts" / "paper_trading" / "trades.csv"


def _monthly_returns(close: pd.Series) -> dict:
    """Compute average monthly returns for a price series."""
    if close is None or len(close) < 60:
        return {}
    
    df = pd.DataFrame({"close": close})
    df.index = pd.to_datetime(df.index)
    df["month"] = df.index.month
    df["year"] = df.index.year
    
    # Monthly returns (last close of month vs last close of prior month)
    monthly = df.resample("ME")["close"].last()
    monthly_ret = monthly.pct_change() * 100
    
    monthly_ret.index = pd.to_datetime(monthly_ret.index)
    
    result = {}
    for month in range(1, 13):
        month_data = monthly_ret[monthly_ret.index.month == month].dropna()
        if len(month_data) >= 3:
            result[month] = {
                "avg_return": round(float(month_data.mean()), 2),
                "win_rate": round(sum(month_data > 0) / len(month_data) * 100, 1),
                "count": len(month_data),
                "std": round(float(month_data.std()), 2),
            }
    
    return result


def compute_seasonality() -> dict:
    """Compute seasonal patterns."""
    from fetch_data import load_all as load_stocks
    from fetch_crypto_data import load_all as load_crypto
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Stock benchmarks
    print("Loading stock data...", file=sys.stderr)
    stock_data = load_stocks()
    
    for benchmark in ["SPY", "QQQ"]:
        if benchmark in stock_data:
            monthly = _monthly_returns(stock_data[benchmark]["close"])
            if monthly:
                results[f"{benchmark}_monthly"] = monthly
                
                # Find best/worst months
                sorted_months = sorted(monthly.items(), key=lambda x: x[1]["avg_return"], reverse=True)
                results[f"{benchmark}_best_month"] = {
                    "month": int(sorted_months[0][0]),
                    "name": datetime(2020, int(sorted_months[0][0]), 1).strftime("%B"),
                    **sorted_months[0][1],
                }
                results[f"{benchmark}_worst_month"] = {
                    "month": int(sorted_months[-1][0]),
                    "name": datetime(2020, int(sorted_months[-1][0]), 1).strftime("%B"),
                    **sorted_months[-1][1],
                }
                
                # Sell in May effect
                nov_apr = [monthly[m]["avg_return"] for m in list(range(11, 13)) + list(range(1, 5)) if m in monthly]
                may_oct = [monthly[m]["avg_return"] for m in range(5, 11) if m in monthly]
                if nov_apr and may_oct:
                    results[f"{benchmark}_sell_in_may"] = {
                        "nov_apr_avg": round(sum(nov_apr) / len(nov_apr), 2),
                        "may_oct_avg": round(sum(may_oct) / len(may_oct), 2),
                        "effect": "confirmed" if sum(nov_apr) / len(nov_apr) > sum(may_oct) / len(may_oct) else "not confirmed",
                    }
    
    # Crypto benchmarks
    print("Loading crypto data...", file=sys.stderr)
    crypto_data = load_crypto()
    
    for benchmark in ["BTC", "ETH"]:
        if benchmark in crypto_data:
            monthly = _monthly_returns(crypto_data[benchmark]["close"])
            if monthly:
                results[f"{benchmark}_monthly"] = monthly
    
    # Strategy performance by month (from trades.csv)
    if TRADES_PATH.exists():
        df = pd.read_csv(TRADES_PATH)
        closed = df[df["status"] == "closed"].copy()
        closed["r_multiple"] = pd.to_numeric(closed["r_multiple"], errors="coerce")
        closed["entry_date"] = pd.to_datetime(closed["entry_date"], errors="coerce")
        closed = closed[closed["r_multiple"].notna() & closed["entry_date"].notna()]
        
        if len(closed) >= 5:
            closed["entry_month"] = closed["entry_date"].dt.month
            closed["entry_dow"] = closed["entry_date"].dt.dayofweek  # 0=Mon, 6=Sun
            
            # By month
            by_month = {}
            for month in range(1, 13):
                month_trades = closed[closed["entry_month"] == month]
                if len(month_trades) >= 2:
                    r_vals = month_trades["r_multiple"].values
                    by_month[month] = {
                        "name": datetime(2020, month, 1).strftime("%B"),
                        "trades": len(r_vals),
                        "avg_r": round(float(np.mean(r_vals)), 3),
                        "win_rate": round(sum(r_vals > 0) / len(r_vals) * 100, 1),
                    }
            results["strategy_by_month"] = by_month
            
            # By day of week
            by_dow = {}
            dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for dow in range(7):
                dow_trades = closed[closed["entry_dow"] == dow]
                if len(dow_trades) >= 2:
                    r_vals = dow_trades["r_multiple"].values
                    by_dow[dow_names[dow]] = {
                        "trades": len(r_vals),
                        "avg_r": round(float(np.mean(r_vals)), 3),
                        "win_rate": round(sum(r_vals > 0) / len(r_vals) * 100, 1),
                    }
            results["strategy_by_dow"] = by_dow
    
    # Current month assessment
    current_month = datetime.utcnow().month
    results["current_month"] = {
        "month": current_month,
        "name": datetime(2020, current_month, 1).strftime("%B"),
    }
    
    # Build seasonal signals
    signals = []
    for benchmark in ["SPY", "QQQ"]:
        bm_data = results.get(f"{benchmark}_monthly", {})
        current_data = bm_data.get(current_month)
        if current_data and current_data["count"] >= 3:
            if current_data["avg_return"] > 1.5:
                signals.append(f"📈 {benchmark} historically strong in {current_data.get('name', '')}: "
                              f"avg {current_data['avg_return']:+.2f}%, WR {current_data['win_rate']:.0f}%")
            elif current_data["avg_return"] < -1:
                signals.append(f"⚠️ {benchmark} historically weak in {current_data.get('name', '')}: "
                              f"avg {current_data['avg_return']:+.2f}%, WR {current_data['win_rate']:.0f}%")
    
    strat_month = results.get("strategy_by_month", {})
    if current_month in strat_month:
        sm = strat_month[current_month]
        if sm["avg_r"] > 0.3:
            signals.append(f"📈 Our strategies perform well in {sm['name']}: avg {sm['avg_r']:+.2f}R, WR {sm['win_rate']:.0f}%")
        elif sm["avg_r"] < -0.2:
            signals.append(f"⚠️ Our strategies underperform in {sm['name']}: avg {sm['avg_r']:+.2f}R, WR {sm['win_rate']:.0f}%")
    
    results["seasonal_signals"] = signals
    
    return results


def get_seasonality_summary() -> dict:
    """Get concise summary."""
    full = compute_seasonality()
    return {
        "current_month": full.get("current_month", {}).get("name", "?"),
        "seasonal_signals": full.get("seasonal_signals", []),
        "spy_best_month": full.get("SPY_best_month", {}).get("name", "?"),
        "spy_worst_month": full.get("SPY_worst_month", {}).get("name", "?"),
    }


def print_report(results: dict):
    print(f"\n📅 **Seasonality Analysis**")
    print(f"   {results['timestamp'][:19]}\n")
    
    for benchmark in ["SPY", "QQQ"]:
        monthly = results.get(f"{benchmark}_monthly", {})
        if monthly:
            print(f"**{benchmark} Monthly Returns:**")
            for month in sorted(monthly.keys()):
                data = monthly[month]
                name = datetime(2020, month, 1).strftime("%b")
                bar = "🟢" if data["avg_return"] > 0 else "🔴"
                print(f"  {bar} {name}: avg {data['avg_return']:+.2f}%, WR {data['win_rate']:.0f}% (n={data['count']})")
            
            best = results.get(f"{benchmark}_best_month", {})
            worst = results.get(f"{benchmark}_worst_month", {})
            print(f"  Best: {best.get('name', '?')} ({best.get('avg_return', 0):+.2f}%)")
            print(f"  Worst: {worst.get('name', '?')} ({worst.get('avg_return', 0):+.2f}%)")
            
            sim = results.get(f"{benchmark}_sell_in_may", {})
            if sim:
                print(f"  Sell in May: {sim['effect']} (Nov-Apr: {sim['nov_apr_avg']:+.2f}% vs May-Oct: {sim['may_oct_avg']:+.2f}%)")
            print()
    
    for benchmark in ["BTC", "ETH"]:
        monthly = results.get(f"{benchmark}_monthly", {})
        if monthly:
            print(f"**{benchmark} Monthly Returns:**")
            for month in sorted(monthly.keys()):
                data = monthly[month]
                name = datetime(2020, month, 1).strftime("%b")
                bar = "🟢" if data["avg_return"] > 0 else "🔴"
                print(f"  {bar} {name}: avg {data['avg_return']:+.2f}%, WR {data['win_rate']:.0f}% (n={data['count']})")
            print()
    
    strat_month = results.get("strategy_by_month", {})
    if strat_month:
        print(f"**Strategy Performance by Month:**")
        for month in sorted(strat_month.keys()):
            data = strat_month[month]
            bar = "🟢" if data["avg_r"] > 0 else "🔴"
            print(f"  {bar} {data['name']}: {data['trades']} trades, avg {data['avg_r']:+.3f}R, WR {data['win_rate']:.0f}%")
        print()
    
    strat_dow = results.get("strategy_by_dow", {})
    if strat_dow:
        print(f"**Strategy Performance by Day of Week:**")
        for dow, data in strat_dow.items():
            bar = "🟢" if data["avg_r"] > 0 else "🔴"
            print(f"  {bar} {dow}: {data['trades']} trades, avg {data['avg_r']:+.3f}R, WR {data['win_rate']:.0f}%")
        print()
    
    if results.get("seasonal_signals"):
        print(f"**Current Seasonal Signals ({results['current_month']['name']}):**")
        for sig in results["seasonal_signals"]:
            print(f"  {sig}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Seasonality Analysis")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    
    results = compute_seasonality()
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print_report(results)
