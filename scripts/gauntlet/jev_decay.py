#!/usr/bin/env python3
"""
Jev Decay Detector — US-151

Replaces heuristic decay_watch.py checks (trailing PF < 1.15, avg R < 0,
slippage > 2x) with Jev classification on the full performance distribution.

Instead of hard thresholds, Jev evaluates:
  1. Is recent performance statistically different from backtest distribution?
  2. Is the strategy losing its edge or just in a drawdown?
  3. What's the probability this strategy should be demoted?

Cost: ~$0.0012 per strategy check (3 questions × $0.0004).

Usage:
    from jev_decay import check_decay
    result = check_decay(strategy_id, trades_csv_path)
"""

import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from jev_client import JevClient


@dataclass
class DecayResult:
    strategy_id: str
    decay_probability: float        # 0-1, probability strategy is decaying
    confidence: float               # model confidence
    recommendation: str             # "demote", "watch", "healthy"
    details: dict[str, Any] = field(default_factory=dict)


def _load_recent_trades(csv_path: Path, n: int = 100) -> list[dict]:
    """Load the most recent N trades from a backtest CSV or trades log."""
    if not csv_path.exists():
        return []
    trades = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            try:
                r_val = float(row.get("r_multiple", row.get("gauntlet_r", 0)))
            except (ValueError, TypeError):
                r_val = 0
            trades.append({
                "r": r_val,
                "date": row.get("date", row.get("exit_date", "")),
                "ticker": row.get("symbol", row.get("ticker", "")),
                "direction": row.get("direction", "long"),
            })
    return trades[-n:]


def _compute_stats(trades: list[dict]) -> dict:
    """Compute summary stats for a set of trades."""
    if not trades:
        return {"count": 0}

    r_values = [t["r"] for t in trades]
    count = len(r_values)
    wins = sum(1 for r in r_values if r > 0)
    losses = sum(1 for r in r_values if r < 0)
    avg_r = sum(r_values) / count
    win_rate = wins / count

    # Streaks
    current_streak = 0
    max_losing_streak = 0
    losing_streak = 0
    for r in r_values:
        if r < 0:
            losing_streak += 1
            max_losing_streak = max(max_losing_streak, losing_streak)
        else:
            losing_streak = 0
    current_streak = losing_streak

    # Profit factor
    gross_wins = sum(r for r in r_values if r > 0)
    gross_losses = abs(sum(r for r in r_values if r < 0))
    profit_factor = gross_wins / gross_losses if gross_losses > 0 else float('inf')

    # Standard deviation
    if count > 1:
        variance = sum((r - avg_r) ** 2 for r in r_values) / (count - 1)
        std_r = math.sqrt(variance)
    else:
        std_r = 0

    return {
        "count": count,
        "avg_r": round(avg_r, 3),
        "std_r": round(std_r, 3),
        "win_rate": round(win_rate, 3),
        "profit_factor": round(profit_factor, 2),
        "current_losing_streak": current_streak,
        "max_losing_streak": max_losing_streak,
    }


def check_decay(strategy_id: str, trades_csv: Optional[Path] = None,
                recent_trades: Optional[list[dict]] = None,
                backtest_stats: Optional[dict] = None,
                jev: Optional[JevClient] = None) -> DecayResult:
    """
    Check if a strategy is decaying using Jev classification.

    Provide either trades_csv (path to CSV) or recent_trades (list of dicts).
    Optionally provide backtest_stats for comparison baseline.

    Returns DecayResult with decay_probability and recommendation.
    """
    if jev is None:
        jev = JevClient()

    # Load trades
    if recent_trades is None and trades_csv is not None:
        recent_trades = _load_recent_trades(trades_csv)
    if recent_trades is None:
        recent_trades = []

    # Compute stats
    stats = _compute_stats(recent_trades)

    # Build state
    state = {
        "strategy_id": strategy_id,
        "recent_stats": stats,
        "backtest_baseline": backtest_stats or {},
    }

    details = {}
    reasons = []

    # Question 1: Decay detection
    try:
        prob = jev.noul(
            state=state,
            instructions="Is this trading strategy's edge decaying or broken? "
                         "Consider: recent avg R vs backtest avg R, win rate trends, "
                         "current losing streak length, profit factor deterioration.",
            true_criteria="Decaying: edge is eroding, recent performance is statistically "
                         "worse than backtest, strategy should be reviewed",
            false_criteria="Healthy: recent performance is within normal variance of "
                          "backtest, drawdown is statistical noise, strategy is working"
        )
        details["decay_probability"] = prob
    except Exception as e:
        details["decay_probability"] = None
        reasons.append(f"Decay check failed: {e}")
        prob = 0.5  # neutral on error

    # Question 2: Drawdown vs breakdown
    try:
        dd_prob = jev.noul(
            state=state,
            instructions="Is the current performance dip just a normal drawdown "
                         "(statistical variance), or does it indicate the edge is broken?",
            true_criteria="Edge broken: structural change, regime shift, or edge decayed "
                         "beyond recovery — demote strategy",
            false_criteria="Normal drawdown: within expected variance, strategy is sound, "
                          "no structural change in market dynamics"
        )
        details["breakdown_probability"] = dd_prob
    except Exception as e:
        details["breakdown_probability"] = None
        dd_prob = 0.5

    # Composite decision
    decay_prob = details.get("decay_probability", 0.5) or 0.5
    breakdown_prob = details.get("breakdown_probability", 0.5) or 0.5

    # Recommendation
    if decay_prob > 0.70 and breakdown_prob > 0.60:
        recommendation = "demote"
    elif decay_prob > 0.45:
        recommendation = "watch"
    else:
        recommendation = "healthy"

    return DecayResult(
        strategy_id=strategy_id,
        decay_probability=decay_prob,
        confidence=max(decay_prob, breakdown_prob),
        recommendation=recommendation,
        details=details,
    )


def check_all_active(jev: Optional[JevClient] = None) -> dict[str, DecayResult]:
    """Run decay check on all active strategies with trade data."""
    if jev is None:
        jev = JevClient()

    results = {}
    results_dir = Path("/root/HermesForge/scripts/validation/results")

    # Find CSVs for active strategies
    for csv_path in sorted(results_dir.glob("*phase1a*.csv")):
        strategy_id = csv_path.stem.split("-phase1a")[0]
        try:
            results[strategy_id] = check_decay(
                strategy_id, trades_csv=csv_path, jev=jev
            )
        except Exception as e:
            results[strategy_id] = DecayResult(
                strategy_id=strategy_id,
                decay_probability=0.5,
                confidence=0,
                recommendation="watch",
                details={"error": str(e)},
            )

    return results


# ── Quick test ──

if __name__ == "__main__":
    import sys
    sid = sys.argv[1] if len(sys.argv) > 1 else "STR-R-crypto"
    csv_path = Path(f"/root/HermesForge/scripts/validation/results/{sid}-phase1a.csv")
    if csv_path.exists():
        result = check_decay(sid, trades_csv=csv_path)
        print(f"Strategy: {result.strategy_id}")
        print(f"Decay probability: {result.decay_probability:.0%}")
        print(f"Recommendation: {result.recommendation}")
        print(f"Details: {result.details}")
    else:
        print(f"No data for {sid}")