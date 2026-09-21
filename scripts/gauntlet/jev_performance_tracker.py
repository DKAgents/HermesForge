#!/usr/bin/env python3
"""
jev_performance_tracker.py — Feedback loop for Jev prefilter

Reads trades.csv and computes per-strategy-type performance stats
that Jev can use to inform signal gating decisions. Updated stats
are lightweight — a few key numbers, not raw trade history.

Feeds into jev_prefilter.py via `get_performance_context()`.

── DESIGN ─────────────────────────────────────────────────────────────
Granularity: per strategy_id (not per-stock — that's too sparse for Jev).
Recency: weighted toward last 30 days, with all-time also available.
Sent to Jev: win_rate, avg_R, trade_count, recent_trend, max_drawdown.
Token budget: ~100 tokens max per strategy in the state dict.
────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

TRADES_CSV = os.path.join(os.path.dirname(__file__), "..", "paper_trading", "trades.csv")


def _load_closed_trades() -> list[dict]:
    """Load closed trades from CSV. Returns parsed dicts with typed values."""
    path = os.path.normpath(TRADES_CSV)
    if not os.path.exists(path):
        return []
    
    trades = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("status") != "closed":
                continue
            # Parse R — prefer gauntlet_r (cost-adjusted), fall back to r_multiple
            gr = row.get("gauntlet_r", "").strip()
            try:
                r_val = float(gr) if gr else float(row.get("r_multiple", 0))
            except (ValueError, TypeError):
                continue
            
            # Parse exit date — force UTC for comparison consistency
            try:
                raw = row["exit_date"].replace(" ", "T").replace("Z", "+00:00")
                exit_dt = datetime.fromisoformat(raw)
                # If naive, assume UTC
                if exit_dt.tzinfo is None:
                    exit_dt = exit_dt.replace(tzinfo=timezone.utc)
            except (ValueError, KeyError):
                continue
            
            trades.append({
                "strategy_id": row.get("strategy_id", "unknown"),
                "r": r_val,
                "exit_dt": exit_dt,
                "is_win": r_val > 0,
            })
    
    return trades


def compute_performance(
    trades: list[dict],
    strategy_id: str,
    lookback_days: int = 30,
) -> dict:
    """
    Compute performance stats for a strategy over a lookback window.
    
    Returns: {win_rate, avg_r, trade_count, total_r, recent_trend, max_dd_r}
    Returns empty dict if no trades in window.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    subset = [t for t in trades if t["strategy_id"] == strategy_id and t["exit_dt"] >= cutoff]
    
    if not subset:
        return {}
    
    rs = [t["r"] for t in subset]
    wins = sum(1 for t in subset if t["is_win"])
    total = len(subset)
    win_rate = wins / total if total > 0 else 0.0
    avg_r = sum(rs) / total
    total_r = sum(rs)
    
    # Trend: compare first half vs second half
    mid = total // 2
    if mid >= 5:
        first_half_avg = sum(rs[:mid]) / mid
        second_half_avg = sum(rs[mid:]) / (total - mid)
        if second_half_avg > first_half_avg + 0.1:
            trend = "improving"
        elif second_half_avg < first_half_avg - 0.1:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"
    
    # Max drawdown in R terms (cumulative)
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in rs:
        cumulative += r
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd
    
    return {
        "win_rate": round(win_rate, 3),
        "avg_r": round(avg_r, 3),
        "trade_count": total,
        "total_r": round(total_r, 2),
        "recent_trend": trend,
        "max_dd_r": round(max_dd, 2),
    }


def get_performance_context(strategy_id: str) -> dict:
    """
    Get compact performance context for Jev prefilter.
    
    Returns dict with 30-day and all-time stats for the strategy.
    Designed to fit within ~100 tokens.
    """
    trades = _load_closed_trades()
    if not trades:
        return {"available": False, "reason": "No closed trades in ledger"}
    
    all_time = compute_performance(trades, strategy_id, lookback_days=9999)
    recent = compute_performance(trades, strategy_id, lookback_days=30)
    
    if not recent and not all_time:
        return {"available": False, "reason": f"No trades for {strategy_id}"}
    
    # If no recent trades, use all-time with a note
    active_perf = recent if recent else all_time
    lookback_label = "30d" if recent else "all_time"
    
    return {
        "available": True,
        f"{lookback_label}_win_rate": active_perf.get("win_rate", 0),
        f"{lookback_label}_avg_r": active_perf.get("avg_r", 0),
        f"{lookback_label}_trade_count": active_perf.get("trade_count", 0),
        f"{lookback_label}_total_r": active_perf.get("total_r", 0),
        f"{lookback_label}_trend": active_perf.get("recent_trend", "unknown"),
        f"{lookback_label}_max_dd_r": active_perf.get("max_dd_r", 0),
        "all_time_trade_count": all_time.get("trade_count", 0),
    }


# ── Quick test ──

if __name__ == "__main__":
    for sid in ["STR-Q-liquidity-sweep", "STR-A-ma-pullback-fibonacci", "STR-B-macd-histogram-divergence"]:
        ctx = get_performance_context(sid)
        print(f"\n{sid}:")
        if ctx.get("available"):
            print(f"  30d: {ctx.get('30d_trade_count',0)} trades, {ctx.get('30d_win_rate',0):.0%} win, {ctx.get('30d_avg_r',0):.3f}R avg, trend={ctx.get('30d_trend','?')}")
            print(f"  all-time: {ctx.get('all_time_trade_count',0)} trades")
        else:
            print(f"  No data: {ctx.get('reason','?')}")