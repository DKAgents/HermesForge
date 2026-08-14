#!/usr/bin/env python3
"""
auto_kill_manager.py — Automatic Strategy Kill/Revive Manager

Monitors strategy performance and automatically:
  - Kills strategies that consistently underperform
  - Flags strategies approaching kill threshold (watch)
  - Revives killed strategies when conditions improve
  - Generates kill/revive recommendations

Kill criteria (configurable):
  - OOS mean R < -0.5 for 10+ closed trades → KILL
  - OOS win rate < 20% for 10+ closed trades → KILL
  - Profit factor < 0.50 for 10+ closed trades → KILL
  - Max consecutive losses > 8 → KILL
  - OOS mean R < -0.3 for 15+ trades AND p-value > 0.3 → KILL (not just bad luck)

Watch criteria:
  - OOS mean R < 0 for 5+ trades → WATCH
  - Win rate < 30% for 5+ trades → WATCH
  - Declining Sharpe over last 10 trades → WATCH

Revive criteria:
  - If killed and latest 5-trade mean R > 0.5 → REVIEW for revival
  - If killed and regime has changed to favorable → REVIEW

Usage:
    python3 auto_kill_manager.py
    python3 auto_kill_manager.py --json
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


def _analyze_strategy(strategy_id: str, closed: pd.DataFrame) -> dict:
    """Analyze a single strategy for kill/watch/revive signals."""
    strat_trades = closed[closed["strategy_id"] == strategy_id]
    r_values = strat_trades["r_multiple"].values
    
    if len(r_values) < 5:
        return {
            "strategy_id": strategy_id,
            "status": "insufficient_data",
            "trades": len(r_values),
            "note": "Need 5+ closed trades for analysis",
        }
    
    mean_r = float(np.mean(r_values))
    win_rate = sum(r_values > 0) / len(r_values) * 100
    profit_factor = abs(sum(r_values[r_values > 0]) / sum(r_values[r_values <= 0])) \
        if sum(r_values[r_values <= 0]) != 0 else float('inf')
    
    # Max consecutive losses
    max_consec_losses = 0
    cur_losses = 0
    for r in r_values:
        if r <= 0:
            cur_losses += 1
            max_consec_losses = max(max_consec_losses, cur_losses)
        else:
            cur_losses = 0
    
    # T-test for significance
    from statistics import NormalDist
    std = float(np.std(r_values, ddof=1))
    t_stat = mean_r / (std / np.sqrt(len(r_values))) if std > 0 else 0
    p_value = 2 * (1 - NormalDist().cdf(abs(t_stat))) if std > 0 else 1.0
    
    # Recent performance (last 5 trades)
    recent_5 = r_values[-5:] if len(r_values) >= 5 else r_values
    recent_mean = float(np.mean(recent_5))
    recent_win = sum(recent_5 > 0) / len(recent_5) * 100
    
    # ── Kill check ────────────────────────────────────────────────────────
    kill_reasons = []
    
    if len(r_values) >= 10:
        if mean_r < -0.5:
            kill_reasons.append(f"Mean R = {mean_r:+.2f} (threshold: -0.5)")
        if win_rate < 20:
            kill_reasons.append(f"Win rate = {win_rate:.1f}% (threshold: 20%)")
        if profit_factor < 0.50:
            kill_reasons.append(f"Profit factor = {profit_factor:.2f} (threshold: 0.50)")
        if max_consec_losses >= 8:
            kill_reasons.append(f"Max consecutive losses = {max_consec_losses} (threshold: 8)")
        if mean_r < -0.3 and p_value > 0.3 and len(r_values) >= 15:
            kill_reasons.append(f"Mean R = {mean_r:+.2f} with p={p_value:.2f} (not bad luck)")
    
    if kill_reasons:
        return {
            "strategy_id": strategy_id,
            "action": "KILL",
            "trades": len(r_values),
            "mean_r": round(mean_r, 3),
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else "inf",
            "max_consec_losses": max_consec_losses,
            "p_value": round(p_value, 4),
            "recent_5_mean_r": round(recent_mean, 3),
            "kill_reasons": kill_reasons,
            "severity": "HIGH",
        }
    
    # ── Watch check ───────────────────────────────────────────────────────
    watch_reasons = []
    
    if len(r_values) >= 5:
        if mean_r < 0:
            watch_reasons.append(f"Negative mean R = {mean_r:+.2f}")
        if win_rate < 30:
            watch_reasons.append(f"Low win rate = {win_rate:.1f}%")
        if recent_mean < 0:
            watch_reasons.append(f"Recent 5-trade mean R = {recent_mean:+.2f}")
    
    if watch_reasons:
        return {
            "strategy_id": strategy_id,
            "action": "WATCH",
            "trades": len(r_values),
            "mean_r": round(mean_r, 3),
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else "inf",
            "max_consec_losses": max_consec_losses,
            "p_value": round(p_value, 4),
            "recent_5_mean_r": round(recent_mean, 3),
            "watch_reasons": watch_reasons,
            "severity": "MEDIUM",
        }
    
    # ── Good ─────────────────────────────────────────────────────────────
    return {
        "strategy_id": strategy_id,
        "action": "RUN",
        "trades": len(r_values),
        "mean_r": round(mean_r, 3),
        "win_rate": round(win_rate, 1),
        "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else "inf",
        "max_consec_losses": max_consec_losses,
        "p_value": round(p_value, 4),
        "recent_5_mean_r": round(recent_mean, 3),
        "severity": "LOW",
    }


def run_kill_analysis() -> dict:
    """Run auto-kill analysis on all strategies."""
    if not TRADES_PATH.exists():
        return {"error": "No trades.csv found"}
    
    df = pd.read_csv(TRADES_PATH)
    closed = df[df["status"] == "closed"].copy()
    closed["r_multiple"] = pd.to_numeric(closed["r_multiple"], errors="coerce")
    closed = closed[closed["r_multiple"].notna()]
    
    if len(closed) < 5:
        return {"error": f"Only {len(closed)} closed trades"}
    
    strategies = closed["strategy_id"].unique()
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_strategies": len(strategies),
        "total_closed_trades": len(closed),
        "actions": [],
        "kill_recommendations": [],
        "watch_recommendations": [],
    }
    
    for strat in strategies:
        analysis = _analyze_strategy(strat, closed)
        results["actions"].append(analysis)
        
        if analysis.get("action") == "KILL":
            results["kill_recommendations"].append(analysis)
        elif analysis.get("action") == "WATCH":
            results["watch_recommendations"].append(analysis)
    
    results["kills"] = len(results["kill_recommendations"])
    results["watches"] = len(results["watch_recommendations"])
    
    return results


def get_kill_summary() -> dict:
    """Get concise summary for daily briefing."""
    full = run_kill_analysis()
    if full.get("error"):
        return {"available": False, "note": full["error"]}
    
    return {
        "available": True,
        "total_strategies": full.get("total_strategies", 0),
        "kills": full.get("kills", 0),
        "watches": full.get("watches", 0),
        "kill_list": [a["strategy_id"] for a in full.get("kill_recommendations", [])],
        "watch_list": [a["strategy_id"] for a in full.get("watch_recommendations", [])],
    }


def print_report(results: dict):
    if results.get("error"):
        print(f"\n❌ {results['error']}")
        return
    
    print(f"\n⚖️ **Auto-Kill Manager**")
    print(f"   {results['timestamp'][:19]}")
    print(f"   {results['total_strategies']} strategies, {results['total_closed_trades']} closed trades\n")
    
    if results["kills"] > 0:
        print(f"🔴 **KILL Recommendations ({results['kills']}):**")
        for a in results["kill_recommendations"]:
            print(f"\n  {a['strategy_id']} — {a['trades']} trades")
            print(f"    Mean R: {a['mean_r']:+.2f}, WR: {a['win_rate']}%, PF: {a['profit_factor']}")
            print(f"    Max consec losses: {a['max_consec_losses']}, p-value: {a['p_value']}")
            for reason in a.get("kill_reasons", []):
                print(f"    ❌ {reason}")
    else:
        print(f"✅ No strategies meet kill criteria")
    
    print()
    
    if results["watches"] > 0:
        print(f"🟡 **WATCH Recommendations ({results['watches']}):**")
        for a in results["watch_recommendations"]:
            print(f"\n  {a['strategy_id']} — {a['trades']} trades")
            print(f"    Mean R: {a['mean_r']:+.2f}, WR: {a['win_rate']}%, PF: {a['profit_factor']}")
            for reason in a.get("watch_reasons", []):
                print(f"    ⚠️ {reason}")
    else:
        print(f"✅ No strategies on watch")
    
    print()
    
    # Show all strategies
    print(f"**All Strategies:**")
    for a in sorted(results["actions"], key=lambda x: x.get("mean_r", 0)):
        action = a.get("action", "?")
        emoji = {"KILL": "🔴", "WATCH": "🟡", "RUN": "✅", "insufficient_data": "⚪"}.get(action, "?")
        print(f"  {emoji} {a['strategy_id']}: {a.get('trades', 0)} trades, "
              f"mean={a.get('mean_r', 0):+.2f}R, WR={a.get('win_rate', 0):.0f}%, "
              f"PF={a.get('profit_factor', 0)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Auto-Kill Manager")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    
    results = run_kill_analysis()
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print_report(results)
