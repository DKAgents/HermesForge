#!/usr/bin/env python3
"""
live_performance_tracker.py — US-112: Live Performance Tracker

Compares live paper trading results against backtest expectations.
Flags when live performance diverges from backtest by >1 standard deviation.

Called automatically when trades close (via capture_signals.py / capture_sweep_signals.py)
or manually for a full report.

Tracks per-strategy and per-level-type:
  - Win rate (actual vs expected)
  - Average R (actual vs expected)
  - Stop-hit rate (actual vs expected)
  - Trade count (is it generating enough signals?)
  - Time since last trade (is the strategy alive?)

Output: JSON status file + console report + Discord alert on divergence

Usage:
    python3 live_performance_tracker.py              # full report
    python3 live_performance_tracker.py --update       # update after trade closes
    python3 live_performance_tracker.py --alert       # post divergence alert to Discord
"""

import sys
import os
import json
import csv
import argparse
import pathlib
import subprocess
from datetime import datetime, timezone, timedelta
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import trade_log

# ── Backtest expectations (from deep backtest results) ──────────────────────
# These are the "truth" the live results are compared against.
# Source: STR-Q deep backtest (696 trades, 1yr Alpaca 5m) + prior backtests for A/B/D/I

BACKTEST_EXPECTATIONS = {
    "STR-Q-liquidity-sweep": {
        "expected_avg_r": 0.597,      # Deep backtest baseline (pre-US-109 caps, which were reverted)
        "expected_win_rate": 46.2,
        "expected_stop_rate": 47.4,
        "expected_target_rate": 30.5,
        "min_trades_for_stats": 20,    # Need 20+ trades before comparing
        "source": "696-trade deep backtest (1yr Alpaca 5m)",
    },
    "STR-B-macd-histogram-divergence": {
        "expected_avg_r": 0.227,
        "expected_win_rate": 40.0,
        "expected_stop_rate": 60.0,
        "expected_target_rate": 30.0,
        "min_trades_for_stats": 15,
        "source": "Phase 1A walk-forward",
    },
    "STR-I-adaptive-trend": {
        "expected_avg_r": 0.15,
        "expected_win_rate": 35.0,
        "expected_stop_rate": 65.0,
        "expected_target_rate": 25.0,
        "min_trades_for_stats": 15,
        "source": "Phase 1A walk-forward (stocks only)",
    },
    "STR-D-sr-role-reversal": {
        "expected_avg_r": 0.033,      # Walk-forward showed no edge
        "expected_win_rate": 35.0,
        "expected_stop_rate": 65.0,
        "expected_target_rate": 25.0,
        "min_trades_for_stats": 15,
        "source": "Phase 1B walk-forward (no edge, p=0.435)",
    },
    "STR-A-ma-pullback-fibonacci": {
        "expected_avg_r": 0.10,
        "expected_win_rate": 35.0,
        "expected_stop_rate": 65.0,
        "expected_target_rate": 30.0,
        "min_trades_for_stats": 15,
        "source": "Phase 1A (killed, minimal edge)",
    },
    "STR-R-alligator": {
        "expected_avg_r": 0.242,
        "expected_win_rate": 35.7,
        "expected_stop_rate": 54.5,
        "expected_target_rate": 18.0,
        "min_trades_for_stats": 20,
        "source": "Phase 1A stocks (510 trades, PF 1.44). Crypto: 280 trades, +0.172R, PF 1.30",
    },
}

# Divergence thresholds (in standard deviations)
DIVERGENCE_SD = 1.5  # Flag if actual is >1.5 SD from expected
MAX_DAYS_SILENT = 7  # Flag if no trades in 7 days

# State file
STATE_FILE = pathlib.Path.home() / ".hermes" / "market_data" / "live_performance.json"

# Discord
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
ALERT_CHANNEL = "1537225420120793088"  # #paper-trading


def _read_all_trades():
    """Read all trades from the trade log CSV."""
    trades = []
    csv_path = trade_log.LOG_PATH
    if not csv_path.exists():
        return trades
    
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            trades.append(r)
    
    return trades


def _compute_live_stats(closed_trades: list, strategy_id: str) -> dict:
    """Compute live trading statistics for a strategy."""
    strat_trades = [t for t in closed_trades if t.get("strategy_id", "") == strategy_id]
    
    if not strat_trades:
        return {
            "n_closed": 0,
            "avg_r": 0,
            "win_rate": 0,
            "stop_rate": 0,
            "target_rate": 0,
            "sum_r": 0,
        }
    
    rs = [float(t.get("r_multiple", 0) or 0) for t in strat_trades]
    n = len(strat_trades)
    wins = sum(1 for r in rs if r > 0)
    stops = sum(1 for t in strat_trades if t.get("exit_reason") == "stop")
    targets = sum(1 for t in strat_trades if t.get("exit_reason") == "target")
    
    return {
        "n_closed": n,
        "avg_r": round(sum(rs) / n, 4) if n > 0 else 0,
        "win_rate": round(wins / n * 100, 1) if n > 0 else 0,
        "stop_rate": round(stops / n * 100, 1) if n > 0 else 0,
        "target_rate": round(targets / n * 100, 1) if n > 0 else 0,
        "sum_r": round(sum(rs), 2),
    }


def _compute_divergence(live: dict, expected: dict, n: int) -> dict:
    """Compute how far live stats diverge from expected.
    
    Returns divergence metrics and flags.
    """
    if n < expected.get("min_trades_for_stats", 15):
        return {
            "sufficient_data": False,
            "message": f"Insufficient data ({n}/{expected['min_trades_for_stats']} trades needed)",
            "flags": [],
        }
    
    # Standard error for win rate (binomial): sqrt(p*(1-p)/n)
    exp_wr = expected["expected_win_rate"] / 100
    se_wr = (exp_wr * (1 - exp_wr) / n) ** 0.5 * 100 if n > 0 else 100
    
    # Standard error for avg R (using sample SD as proxy)
    # Use a rough estimate: SE ≈ SD / sqrt(n), with SD ≈ 1.5R for R-multiple distributions
    se_r = 1.5 / (n ** 0.5) if n > 0 else 10
    
    flags = []
    
    # Win rate divergence
    wr_delta = live["win_rate"] - expected["expected_win_rate"]
    wr_z = wr_delta / se_wr if se_wr > 0 else 0
    if abs(wr_z) > DIVERGENCE_SD:
        direction = "above" if wr_delta > 0 else "below"
        flags.append({
            "metric": "win_rate",
            "expected": expected["expected_win_rate"],
            "actual": live["win_rate"],
            "delta": round(wr_delta, 1),
            "z_score": round(wr_z, 2),
            "severity": "HIGH" if abs(wr_z) > 2 else "MEDIUM",
            "message": f"Win rate {live['win_rate']}% is {direction} expected {expected['expected_win_rate']}% (z={wr_z:.2f})",
        })
    
    # Avg R divergence
    r_delta = live["avg_r"] - expected["expected_avg_r"]
    r_z = r_delta / se_r if se_r > 0 else 0
    if abs(r_z) > DIVERGENCE_SD:
        direction = "above" if r_delta > 0 else "below"
        flags.append({
            "metric": "avg_r",
            "expected": expected["expected_avg_r"],
            "actual": live["avg_r"],
            "delta": round(r_delta, 4),
            "z_score": round(r_z, 2),
            "severity": "HIGH" if abs(r_z) > 2 else "MEDIUM",
            "message": f"Avg R {live['avg_r']:+.4f} is {direction} expected {expected['expected_avg_r']:+.4f} (z={r_z:.2f})",
        })
    
    # Stop rate divergence
    stop_delta = live["stop_rate"] - expected["expected_stop_rate"]
    stop_z = stop_delta / se_wr if se_wr > 0 else 0  # reuse binomial SE
    if abs(stop_z) > DIVERGENCE_SD:
        flags.append({
            "metric": "stop_rate",
            "expected": expected["expected_stop_rate"],
            "actual": live["stop_rate"],
            "delta": round(stop_delta, 1),
            "z_score": round(stop_z, 2),
            "severity": "HIGH" if abs(stop_z) > 2 else "MEDIUM",
            "message": f"Stop rate {live['stop_rate']}% vs expected {expected['expected_stop_rate']}% (z={stop_z:.2f})",
        })
    
    return {
        "sufficient_data": True,
        "flags": flags,
        "se_wr": round(se_wr, 2),
        "se_r": round(se_r, 4),
    }


def _check_silent_strategies(all_trades: list) -> list:
    """Check if any strategy hasn't produced trades in a while."""
    silent = []
    now = datetime.now(timezone.utc)
    
    for strat_id, expected in BACKTEST_EXPECTATIONS.items():
        strat_trades = [t for t in all_trades if t.get("strategy_id", "") == strat_id]
        if not strat_trades:
            silent.append({
                "strategy_id": strat_id,
                "days_silent": 999,
                "message": f"No trades ever for {strat_id}",
            })
            continue
        
        # Check most recent trade (open or closed)
        latest_date = max(t.get("entry_date", "2000-01-01") for t in strat_trades)
        try:
            latest_dt = datetime.strptime(latest_date[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days = (now - latest_dt).days
            if days > MAX_DAYS_SILENT:
                silent.append({
                    "strategy_id": strat_id,
                    "days_silent": days,
                    "message": f"No trades in {days} days for {strat_id}",
                })
        except (ValueError, TypeError):
            pass
    
    return silent


def generate_report() -> dict:
    """Generate full live performance report."""
    all_trades = _read_all_trades()
    closed = [t for t in all_trades if t.get("status") == "closed"]
    open_trades = [t for t in all_trades if t.get("status") == "open"]
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_trades": len(all_trades),
        "open_trades": len(open_trades),
        "closed_trades": len(closed),
        "strategies": {},
        "silent_strategies": [],
        "all_flags": [],
    }
    
    # Per-strategy analysis
    for strat_id, expected in BACKTEST_EXPECTATIONS.items():
        live = _compute_live_stats(closed, strat_id)
        divergence = _compute_divergence(live, expected, live["n_closed"])
        
        report["strategies"][strat_id] = {
            "expected": expected,
            "live": live,
            "divergence": divergence,
        }
        
        # Collect flags
        if divergence.get("flags"):
            for flag in divergence["flags"]:
                flag["strategy_id"] = strat_id
                report["all_flags"].append(flag)
    
    # Silent strategies
    report["silent_strategies"] = _check_silent_strategies(all_trades)
    for s in report["silent_strategies"]:
        report["all_flags"].append({
            "strategy_id": s["strategy_id"],
            "metric": "silent",
            "severity": "HIGH",
            "message": s["message"],
        })
    
    return report


def post_divergence_alert(report: dict):
    """Post a Discord alert if there are any divergence flags."""
    flags = report.get("all_flags", [])
    if not flags:
        return False
    
    if not DISCORD_BOT_TOKEN:
        print("  ⚠️ DISCORD_BOT_TOKEN not set — skipping alert")
        return False
    
    # Build alert message
    high_flags = [f for f in flags if f.get("severity") == "HIGH"]
    medium_flags = [f for f in flags if f.get("severity") == "MEDIUM"]
    
    lines = []
    lines.append(f"🚨 **Live Performance Divergence Alert** ({len(flags)} flags)")
    lines.append(f"📊 {report['closed_trades']} closed trades, {report['open_trades']} open\n")
    
    if high_flags:
        lines.append("**HIGH severity:**")
        for f in high_flags:
            lines.append(f"  • `{f['strategy_id']}` — {f['message']}")
    
    if medium_flags:
        lines.append("\n**MEDIUM severity:**")
        for f in medium_flags:
            lines.append(f"  • `{f['strategy_id']}` — {f['message']}")
    
    # Per-strategy summary
    lines.append("\n**Per-Strategy Summary:**")
    for strat_id, data in report["strategies"].items():
        live = data["live"]
        exp = data["expected"]
        div = data["divergence"]
        
        if not div.get("sufficient_data"):
            lines.append(f"  `{strat_id}`: {live['n_closed']}/{exp['min_trades_for_stats']} trades — insufficient data")
        else:
            status = "✅" if not div.get("flags") else "⚠️"
            lines.append(
                f"  {status} `{strat_id}`: {live['n_closed']} trades, "
                f"WR={live['win_rate']}% (exp {exp['expected_win_rate']}%), "
                f"R={live['avg_r']:+.3f} (exp {exp['expected_avg_r']:+.3f})"
            )
    
    embed = {
        "title": "🚨 Live Performance Tracker",
        "description": "\n".join(lines),
        "color": 0xe74c3c if high_flags else 0xf1c40f,
        "footer": {"text": "HermesForge US-112 Live Performance Tracker"},
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
    }
    
    payload = {"embeds": [embed]}
    url = f"https://discord.com/api/v10/channels/{ALERT_CHANNEL}/messages"
    cmd = [
        "curl", "-s", "-X", "POST",
        "-H", f"Authorization: Bot {DISCORD_BOT_TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload),
        url,
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        response = json.loads(result.stdout)
        if "id" in response:
            print("  📢 Divergence alert posted to Discord")
            return True
        else:
            print(f"  ⚠️ Discord post failed: {result.stdout[:200]}")
            return False
    except Exception as e:
        print(f"  ⚠️ Discord post error: {e}")
        return False


def save_report(report: dict):
    """Save report to state file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(report, f, indent=2, default=str)


def main():
    ap = argparse.ArgumentParser(description="US-112: Live Performance Tracker")
    ap.add_argument("--update", action="store_true", help="Update report (called after trade closes)")
    ap.add_argument("--alert", action="store_true", help="Post divergence alert to Discord")
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    args = ap.parse_args()
    
    report = generate_report()
    save_report(report)
    
    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return
    
    # Console report
    print("=== US-112: Live Performance Tracker ===\n")
    print(f"Total: {report['total_trades']} trades ({report['closed_trades']} closed, {report['open_trades']} open)")
    
    print(f"\n── Per-Strategy Performance ──")
    for strat_id, data in report["strategies"].items():
        live = data["live"]
        exp = data["expected"]
        div = data["divergence"]
        
        if not div.get("sufficient_data"):
            print(f"\n  {strat_id}")
            print(f"    Status: INSUFFICIENT DATA ({live['n_closed']}/{exp['min_trades_for_stats']} trades)")
            print(f"    Source: {exp['source']}")
        else:
            print(f"\n  {strat_id}")
            print(f"    Trades: {live['n_closed']}")
            print(f"    Win Rate: {live['win_rate']}% (expected {exp['expected_win_rate']}%)")
            print(f"    Avg R: {live['avg_r']:+.4f} (expected {exp['expected_avg_r']:+.4f})")
            print(f"    Stop Rate: {live['stop_rate']}% (expected {exp['expected_stop_rate']}%)")
            print(f"    Sum R: {live['sum_r']:+.1f}")
            
            if div.get("flags"):
                for flag in div["flags"]:
                    print(f"    {'⚠️' if flag['severity'] == 'MEDIUM' else '🚨'} {flag['message']}")
            else:
                print(f"    ✅ No divergence detected")
    
    if report["silent_strategies"]:
        print(f"\n── Silent Strategies (>{MAX_DAYS_SILENT} days no trades) ──")
        for s in report["silent_strategies"]:
            print(f"  {s['strategy_id']}: {s['message']}")
    
    if report["all_flags"]:
        print(f"\n── All Flags ({len(report['all_flags'])}) ──")
        for f in report["all_flags"]:
            print(f"  [{f['severity']}] {f['strategy_id']}: {f['message']}")
    else:
        print(f"\n✅ No flags — all strategies performing within expected parameters")
    
    if args.alert and report["all_flags"]:
        print(f"\n── Posting Discord Alert ──")
        post_divergence_alert(report)
    
    print(f"\nReport saved to {STATE_FILE}")


if __name__ == "__main__":
    main()