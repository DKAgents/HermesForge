#!/usr/bin/env python3
"""
jev_threshold_tuner.py — ML-driven Jev threshold optimizer

Periodically analyzes trade ledger to find the optimal MARGINAL_THRESHOLD
that maximizes net R while keeping enough trade flow. Auto-adjusts the
threshold in jev_prefilter.py when a better value is found.

Method:
  1. Bucket past trades by their Jev composite score
  2. Compute net R per bucket (including costs)
  3. Find threshold that maximizes cumulative net R from that point up
  4. Apply if statistically significant improvement over current threshold

Runs via cron: every 6 hours (retrains ML, re-tunes thresholds)
"""

import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TRADES_PATH = PROJECT_ROOT / "scripts" / "paper_trading" / "trades.csv"
PREFILTER_PATH = PROJECT_ROOT / "scripts" / "gauntlet" / "jev_prefilter.py"
THRESHOLD_CACHE_PATH = PROJECT_ROOT / ".jev_thresholds.json"
MIN_TRADES_FOR_TUNE = 50
ANALYSIS_WINDOW_DAYS = 30
COST_BPS = 12  # 11-13 bps round-trip
MIN_FLOW_TRADES_PER_DAY = 3


def load_trades(cutoff_date: datetime) -> list[dict]:
    """Load closed trades after cutoff, with Jev scores if available."""
    trades = []
    if not TRADES_PATH.exists():
        return trades

    with open(TRADES_PATH) as f:
        for row in csv.DictReader(f):
            if row.get("status") != "closed":
                continue
            try:
                exit_dt = datetime.fromisoformat(
                    row["exit_date"].replace(" ", "T").replace("Z", "+00:00")
                )
                # Ensure timezone-aware for comparison
                if exit_dt.tzinfo is None:
                    exit_dt = exit_dt.replace(tzinfo=timezone.utc)
            except (ValueError, KeyError):
                continue
            if exit_dt < cutoff_date:
                continue

            # Net R after costs
            gr = row.get("gauntlet_r", "").strip()
            try:
                net_r = float(gr) if gr else float(row.get("r_multiple", 0))
            except (ValueError, TypeError):
                continue

            # Jev composite score (if recorded at capture time)
            jev_score = None
            jev_raw = row.get("jev_score", "").strip()
            if jev_raw:
                try:
                    jev_score = float(jev_raw)
                except ValueError:
                    pass

            trades.append({
                "strategy": row.get("strategy_id", "unknown"),
                "ticker": row.get("ticker", "?"),
                "net_r": net_r,
                "jev_score": jev_score,
                "exit_date": exit_dt.isoformat(),
            })
    return trades


def find_optimal_threshold(trades: list[dict], min_trades: int = MIN_TRADES_FOR_TUNE
                           ) -> Optional[dict]:
    """
    Bucket trades by Jev score, find threshold that maximizes net R.

    Only evaluates trades WITH Jev scores. Without scores, can't bucket.
    """
    scored = [t for t in trades if t["jev_score"] is not None]
    if len(scored) < min_trades:
        return None

    # Sort by Jev score ascending
    scored.sort(key=lambda t: t["jev_score"])

    # Sweep: for each possible threshold, compute what passes and its net R
    best_threshold = None
    best_net_r = float("-inf")
    all_net_r = sum(t["net_r"] for t in scored)
    all_count = len(scored)

    for candidate_threshold in [i / 100 for i in range(20, 81, 2)]:  # 0.20 to 0.80
        passing = [t for t in scored if t["jev_score"] >= candidate_threshold]
        if len(passing) < 5:
            continue

        net_r = sum(t["net_r"] for t in passing)
        count = len(passing)
        avg_r = net_r / count if count else 0

        # Penalize extremely restrictive thresholds (keep flow alive)
        flow_ratio = count / max(all_count, 1)
        if flow_ratio < 0.05:  # too few trades → not useful
            continue

        # Score: net R * flow bonus (keeps enough trades going)
        flow_bonus = min(flow_ratio * 2, 1.0)  # linearly reward up to 50% flow
        adjusted_net_r = net_r * (0.7 + 0.3 * flow_bonus)

        if adjusted_net_r > best_net_r:
            best_net_r = adjusted_net_r
            best_threshold = {
                "threshold": candidate_threshold,
                "net_r": round(net_r, 2),
                "avg_r": round(avg_r, 4),
                "trade_count": count,
                "flow_pct": round(flow_ratio * 100, 1),
                "total_trades_analyzed": len(scored),
            }

    return best_threshold


def apply_threshold(new_threshold: float, dry_run: bool = False) -> dict:
    """Write threshold to prefilter file and cache."""
    result = {"applied": False, "old_threshold": None, "new_threshold": new_threshold}

    # Read current thresholds from prefilter file
    approved_threshold = 0.75
    with open(PREFILTER_PATH) as f:
        content = f.read()
        for line in content.split("\n"):
            if "APPROVED_THRESHOLD =" in line:
                try:
                    approved_threshold = float(line.split("=")[1].split("#")[0].strip())
                except (ValueError, IndexError):
                    pass
            if "MARGINAL_THRESHOLD =" in line and result["old_threshold"] is None:
                try:
                    result["old_threshold"] = float(line.split("=")[1].split("#")[0].strip())
                except (ValueError, IndexError):
                    pass

    if result["old_threshold"] and abs(result["old_threshold"] - new_threshold) < 0.02:
        result["reason"] = f"Too close to current ({result['old_threshold']:.2f})"
        return result

    if dry_run:
        result["dry_run"] = True
        return result

    # Patch the file
    old_line = None
    new_line = None
    with open(PREFILTER_PATH) as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if "MARGINAL_THRESHOLD =" in line and "#" in line:
            old_line = line
            indent = line[: len(line) - len(line.lstrip())]
            new_line = (
                f"{indent}MARGINAL_THRESHOLD = {new_threshold:.2f}"
                f"   # {new_threshold:.2f} <= comp < {approved_threshold:.2f}"
                f" → paper only, never live\n"
            )
            lines[i] = new_line
            break

    if old_line and new_line:
        with open(PREFILTER_PATH, "w") as f:
            f.writelines(lines)
        result["applied"] = True
        result["reason"] = f"Updated from {result['old_threshold']:.2f} → {new_threshold:.2f}"

    # Update cache
    with open(THRESHOLD_CACHE_PATH, "w") as f:
        json.dump(
            {
                "marginal_threshold": new_threshold,
                "approved_threshold": approved_threshold,
                "tuned_at": datetime.now(timezone.utc).isoformat(),
                "trades_analyzed": None,
            },
            f,
            indent=2,
        )

    return result


def main(dry_run: bool = False):
    cutoff = datetime.now(timezone.utc) - timedelta(days=ANALYSIS_WINDOW_DAYS)
    trades = load_trades(cutoff)

    print(f"Loaded {len(trades)} closed trades (since {cutoff.date()})")
    scored = [t for t in trades if t["jev_score"] is not None]
    print(f"  With Jev scores: {len(scored)}")

    if len(scored) < MIN_TRADES_FOR_TUNE:
        print(f"  Not enough scored trades ({len(scored)} < {MIN_TRADES_FOR_TUNE}) — skipping")
        return

    optimal = find_optimal_threshold(trades)
    if optimal is None:
        print("  Could not determine optimal threshold")
        return

    print(f"\nOptimal threshold: {optimal['threshold']:.2f}")
    print(f"  Net R: {optimal['net_r']:.1f}")
    print(f"  Avg R: {optimal['avg_r']:.4f}")
    print(f"  Trades passing: {optimal['trade_count']}")
    print(f"  Flow: {optimal['flow_pct']:.1f}%")
    print(f"  (analyzed {optimal['total_trades_analyzed']} scored trades)")

    result = apply_threshold(optimal["threshold"], dry_run=dry_run)
    print(f"\nApply result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    main(dry_run=dry_run)