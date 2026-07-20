#!/usr/bin/env python3
"""
performance_report.py — HermesForge EPIC-010 (US-071)

Reads trades.csv and produces an evidence-based paper trading performance
summary: open positions/heat, recently closed trades, and running totals
by strategy and asset class. No editorializing on small sample sizes --
states counts plainly per the user's evidence-based analysis preference.

Usage:
    python3 performance_report.py [--since-hours N]
"""

import sys
import argparse
import pathlib
import datetime

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import trade_log


def _rows() -> list[dict]:
    return trade_log._read_all_rows()


def build_report(since_hours: int = 24) -> str:
    rows = _rows()
    open_rows = [r for r in rows if r["status"] == "open"]
    closed_rows = [r for r in rows if r["status"] == "closed"]

    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=since_hours)
    recent_closed = []
    for r in closed_rows:
        try:
            exit_dt = datetime.datetime.fromisoformat(r["exit_date"])
        except (ValueError, TypeError):
            continue
        if exit_dt >= cutoff:
            recent_closed.append(r)

    lines = ["📈 **Paper Trading Performance Report**\n"]

    # --- Open positions ---
    total_heat = sum(float(r.get("position_size_pct", 0) or 0) for r in open_rows)
    lines.append(f"**Open Positions:** {len(open_rows)} (aggregate heat: {total_heat:.2f}%)")
    if open_rows:
        by_strategy = {}
        for r in open_rows:
            by_strategy.setdefault(r["strategy_id"], []).append(r)
        for sid, trades in by_strategy.items():
            lines.append(f"  • {sid}: {len(trades)} open ({', '.join(t['ticker'] for t in trades)})")
    lines.append("")

    # --- Recently closed ---
    lines.append(f"**Closed (last {since_hours}h):** {len(recent_closed)}")
    if recent_closed:
        wins = [r for r in recent_closed if float(r.get("r_multiple", 0) or 0) > 0]
        win_rate = len(wins) / len(recent_closed) * 100
        avg_r = sum(float(r.get("r_multiple", 0) or 0) for r in recent_closed) / len(recent_closed)
        lines.append(f"  Win rate: {win_rate:.0f}% ({len(wins)}/{len(recent_closed)}) | Avg R: {avg_r:+.2f}")

        best = max(recent_closed, key=lambda r: float(r.get("r_multiple", 0) or 0))
        worst = min(recent_closed, key=lambda r: float(r.get("r_multiple", 0) or 0))
        lines.append(f"  Best: {best['ticker']} ({best['strategy_id']}) {float(best['r_multiple']):+.2f}R")
        lines.append(f"  Worst: {worst['ticker']} ({worst['strategy_id']}) {float(worst['r_multiple']):+.2f}R")
    lines.append("")

    # --- Running totals since inception, by strategy ---
    lines.append("**Running Totals (since inception):**")
    if not closed_rows:
        lines.append("  No closed trades yet.")
    else:
        by_strategy_all = {}
        for r in closed_rows:
            by_strategy_all.setdefault(r["strategy_id"], []).append(r)
        for sid, trades in sorted(by_strategy_all.items()):
            wins = [t for t in trades if float(t.get("r_multiple", 0) or 0) > 0]
            wr = len(wins) / len(trades) * 100
            avg_r = sum(float(t.get("r_multiple", 0) or 0) for t in trades) / len(trades)
            lines.append(f"  • {sid}: {len(trades)} trades, {wr:.0f}% win rate, avg R {avg_r:+.2f}")

        # By asset class
        lines.append("")
        lines.append("**By Asset Class:**")
        by_class = {}
        for r in closed_rows:
            by_class.setdefault(r.get("asset_class", "unknown"), []).append(r)
        for ac, trades in sorted(by_class.items()):
            wins = [t for t in trades if float(t.get("r_multiple", 0) or 0) > 0]
            wr = len(wins) / len(trades) * 100
            avg_r = sum(float(t.get("r_multiple", 0) or 0) for t in trades) / len(trades)
            lines.append(f"  • {ac}: {len(trades)} trades, {wr:.0f}% win rate, avg R {avg_r:+.2f}")

    if len(closed_rows) < 10:
        lines.append("")
        lines.append(f"_Note: only {len(closed_rows)} closed trades total -- sample size too small for reliable conclusions._")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="HermesForge paper trading performance report")
    ap.add_argument("--since-hours", type=int, default=24)
    args = ap.parse_args()
    print(build_report(since_hours=args.since_hours))


if __name__ == "__main__":
    main()
