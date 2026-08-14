#!/usr/bin/env python3
"""
compute_risk_metrics.py — Paper Portfolio Risk Metrics Dashboard

Computes professional risk metrics for the paper trading portfolio:
  - Sharpe Ratio (annualized)
  - Sortino Ratio (downside-deviation-adjusted)
  - Maximum Drawdown (peak-to-trough)
  - Calmar Ratio (annualized return / max DD)
  - Win Rate, Profit Factor, Expectancy
  - Average Win / Average Loss ratio
  - Longest winning/losing streaks
  - Current portfolio heat
  - Open vs closed trade breakdown

Usage:
    python3 compute_risk_metrics.py
    python3 compute_risk_metrics.py --json
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


def compute_metrics() -> dict:
    """Compute all risk metrics from trades.csv."""
    if not TRADES_PATH.exists():
        return {"error": "No trades.csv found"}
    
    df = pd.read_csv(TRADES_PATH)
    df["r_multiple"] = pd.to_numeric(df["r_multiple"], errors="coerce")
    df["position_size_pct"] = pd.to_numeric(df["position_size_pct"], errors="coerce")
    
    closed = df[df["status"] == "closed"].copy()
    open_trades = df[df["status"] == "open"].copy()
    
    closed = closed[closed["r_multiple"].notna()]
    
    if len(closed) < 3:
        return {"error": f"Only {len(closed)} closed trades — insufficient for metrics"}
    
    r_values = closed["r_multiple"].values
    
    # ── Basic stats ──────────────────────────────────────────────────────
    wins = r_values[r_values > 0]
    losses = r_values[r_values <= 0]
    
    win_rate = len(wins) / len(r_values) * 100
    avg_win = float(np.mean(wins)) if len(wins) > 0 else 0
    avg_loss = float(np.mean(losses)) if len(losses) > 0 else 0
    expectancy = float(np.mean(r_values))
    
    profit_factor = abs(sum(wins) / sum(losses)) if sum(losses) != 0 else float('inf')
    
    # ── Sharpe & Sortino (using R multiples as proxy for returns) ────────
    # Annualize assuming ~250 trading days, ~10 trades/month = 120/year
    trades_per_year = 120
    mean_r = float(np.mean(r_values))
    std_r = float(np.std(r_values, ddof=1))
    
    sharpe = (mean_r / std_r * np.sqrt(trades_per_year)) if std_r > 0 else 0
    
    # Sortino: only downside deviation
    downside = r_values[r_values < 0]
    downside_std = float(np.std(downside, ddof=1)) if len(downside) > 1 else std_r
    sortino = (mean_r / downside_std * np.sqrt(trades_per_year)) if downside_std > 0 else 0
    
    # ── Equity curve and max drawdown ────────────────────────────────────
    equity = np.cumsum(r_values)
    running_max = np.maximum.accumulate(equity)
    drawdowns = equity - running_max
    max_dd = float(np.min(drawdowns))
    max_dd_pct = float(max_dd / running_max[np.argmin(drawdowns)] * 100) if running_max[np.argmin(drawdowns)] != 0 else 0
    
    # Total R
    total_r = float(np.sum(r_values))
    
    # ── Calmar (annualized return / max DD) ───────────────────────────────
    # Annualized return in R terms
    annual_r = mean_r * trades_per_year
    calmar = abs(annual_r / max_dd) if max_dd != 0 else 0
    
    # ── Streaks ──────────────────────────────────────────────────────────
    current_streak = 0
    streak_type = "none"
    best_win_streak = 0
    worst_loss_streak = 0
    cur_win = 0
    cur_loss = 0
    
    for r in r_values:
        if r > 0:
            cur_win += 1
            cur_loss = 0
            best_win_streak = max(best_win_streak, cur_win)
        else:
            cur_loss += 1
            cur_win = 0
            worst_loss_streak = max(worst_loss_streak, cur_loss)
    
    # Current streak (from end)
    if len(r_values) > 0:
        last_r = r_values[-1]
        current_streak = 1
        for i in range(len(r_values) - 2, -1, -1):
            if (r_values[i] > 0 and last_r > 0) or (r_values[i] <= 0 and last_r <= 0):
                current_streak += 1
                last_r = r_values[i]
            else:
                break
        streak_type = "winning" if r_values[-1] > 0 else "losing"
    
    # ── Per-strategy breakdown ────────────────────────────────────────────
    per_strategy = {}
    for strat in closed["strategy_id"].unique():
        strat_trades = closed[closed["strategy_id"] == strat]
        strat_r = strat_trades["r_multiple"].values
        strat_wins = strat_r[strat_r > 0]
        per_strategy[strat] = {
            "trades": len(strat_r),
            "win_rate": round(len(strat_wins) / len(strat_r) * 100, 1) if len(strat_r) > 0 else 0,
            "avg_r": round(float(np.mean(strat_r)), 3),
            "total_r": round(float(np.sum(strat_r)), 2),
            "profit_factor": round(abs(sum(strat_wins) / sum(strat_r[strat_r <= 0])), 2)
                             if sum(strat_r[strat_r <= 0]) != 0 else float('inf'),
        }
    
    # ── Portfolio heat ───────────────────────────────────────────────────
    open_heat = float(open_trades["position_size_pct"].sum()) if len(open_trades) > 0 else 0
    
    # ── By direction ─────────────────────────────────────────────────────
    long_trades = closed[closed["direction"] == "long"]
    short_trades = closed[closed["direction"] == "short"]
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_trades": len(df),
        "closed_trades": len(closed),
        "open_trades": len(open_trades),
        "portfolio_heat": round(open_heat, 2),
        
        # Returns
        "total_r": round(total_r, 2),
        "avg_r": round(mean_r, 3),
        "expectancy": round(expectancy, 3),
        
        # Risk-adjusted
        "sharpe": round(sharpe, 2),
        "sortino": round(sortino, 2),
        "calmar": round(calmar, 2),
        
        # Drawdown
        "max_drawdown_r": round(max_dd, 2),
        "max_drawdown_pct": round(max_dd_pct, 1),
        "current_equity_r": round(float(equity[-1]), 2),
        
        # Win/Loss
        "win_rate": round(win_rate, 1),
        "avg_win_r": round(avg_win, 3),
        "avg_loss_r": round(avg_loss, 3),
        "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else "inf",
        "win_loss_ratio": round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0,
        
        # Streaks
        "best_win_streak": best_win_streak,
        "worst_loss_streak": worst_loss_streak,
        "current_streak": current_streak,
        "current_streak_type": streak_type,
        
        # Per-strategy
        "per_strategy": per_strategy,
        
        # Direction
        "long_trades": len(long_trades),
        "long_win_rate": round(len(long_trades[long_trades["r_multiple"] > 0]) / len(long_trades) * 100, 1)
                        if len(long_trades) > 0 else 0,
        "long_avg_r": round(float(long_trades["r_multiple"].mean()), 3) if len(long_trades) > 0 else 0,
        "short_trades": len(short_trades),
        "short_win_rate": round(len(short_trades[short_trades["r_multiple"] > 0]) / len(short_trades) * 100, 1)
                         if len(short_trades) > 0 else 0,
        "short_avg_r": round(float(short_trades["r_multiple"].mean()), 3) if len(short_trades) > 0 else 0,
    }


def get_risk_summary() -> dict:
    """Get concise summary for regime filter / daily briefing."""
    full = compute_metrics()
    if full.get("error"):
        return {"available": False, "note": full["error"]}
    
    return {
        "available": True,
        "total_r": full.get("total_r", 0),
        "sharpe": full.get("sharpe", 0),
        "sortino": full.get("sortino", 0),
        "max_dd_r": full.get("max_drawdown_r", 0),
        "win_rate": full.get("win_rate", 0),
        "profit_factor": full.get("profit_factor", 0),
        "expectancy": full.get("expectancy", 0),
        "portfolio_heat": full.get("portfolio_heat", 0),
        "open_trades": full.get("open_trades", 0),
    }


def print_report(metrics: dict):
    if metrics.get("error"):
        print(f"\n❌ {metrics['error']}")
        return
    
    print(f"\n📊 **Portfolio Risk Metrics Dashboard**")
    print(f"   {metrics['timestamp'][:19]}\n")
    
    print(f"**Overview:**")
    print(f"  Total trades: {metrics['total_trades']} ({metrics['closed_trades']} closed, {metrics['open_trades']} open)")
    print(f"  Portfolio heat: {metrics['portfolio_heat']}%")
    print()
    
    print(f"**Returns:**")
    print(f"  Total R: {metrics['total_r']:+.2f}R")
    print(f"  Avg R per trade: {metrics['avg_r']:+.3f}R (expectancy)")
    print()
    
    print(f"**Risk-Adjusted:**")
    print(f"  Sharpe: {metrics['sharpe']:.2f}")
    print(f"  Sortino: {metrics['sortino']:.2f}")
    print(f"  Calmar: {metrics['calmar']:.2f}")
    print(f"  Max Drawdown: {metrics['max_drawdown_r']:.2f}R ({metrics['max_drawdown_pct']:.1f}%)")
    print(f"  Current equity: {metrics['current_equity_r']:+.2f}R")
    print()
    
    print(f"**Win/Loss:**")
    print(f"  Win rate: {metrics['win_rate']:.1f}%")
    print(f"  Avg win: {metrics['avg_win_r']:+.3f}R | Avg loss: {metrics['avg_loss_r']:+.3f}R")
    print(f"  Win/loss ratio: {metrics['win_loss_ratio']:.2f}")
    print(f"  Profit factor: {metrics['profit_factor']}")
    print()
    
    print(f"**Streaks:**")
    print(f"  Best win streak: {metrics['best_win_streak']}")
    print(f"  Worst loss streak: {metrics['worst_loss_streak']}")
    print(f"  Current: {metrics['current_streak']} {metrics['current_streak_type']}")
    print()
    
    print(f"**Direction:**")
    print(f"  Long: {metrics['long_trades']} trades, WR={metrics['long_win_rate']:.1f}%, avg={metrics['long_avg_r']:+.3f}R")
    print(f"  Short: {metrics['short_trades']} trades, WR={metrics['short_win_rate']:.1f}%, avg={metrics['short_avg_r']:+.3f}R")
    print()
    
    print(f"**Per-Strategy:**")
    for strat, data in sorted(metrics["per_strategy"].items(), key=lambda x: x[1]["total_r"], reverse=True):
        print(f"  {strat}: {data['trades']} trades, WR={data['win_rate']:.1f}%, "
              f"avg={data['avg_r']:+.3f}R, total={data['total_r']:+.2f}R, PF={data['profit_factor']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Portfolio Risk Metrics")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    
    metrics = compute_metrics()
    if args.json:
        print(json.dumps(metrics, indent=2, default=str))
    else:
        print_report(metrics)
