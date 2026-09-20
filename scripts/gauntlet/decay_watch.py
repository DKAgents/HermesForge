"""
Decay Watch Module (PROP-001 G6/G7).
Scheduled recomputation of rolling stats for every Active strategy.

Applies pre-registered kill rules:
- Trailing 100-trade PF < 1.15 → demote Active→Hypotheses
- Trailing 20-trade avg R < 0 for 2 consecutive non-overlapping windows → demote
- Realised slippage > 2x modelled for 20 consecutive trades → demote
"""

from __future__ import annotations

import csv
import math
from typing import Any, Dict, List, Optional, Tuple


# ── Thresholds ───────────────────────────────────────────────────────────────
PF_THRESHOLD = 1.15
PF_WINDOW = 100

AVG_R_WINDOW = 20
AVG_R_THRESHOLD = 0.0
AVG_R_CONSECUTIVE = 2

SLIPPAGE_WINDOW = 20
SLIPPAGE_RATIO = 2.0


def check_decay(
    strategy_id: str,
    trades: List[Dict[str, Any]],
    pf_window: int = PF_WINDOW,
    avg_r_window: int = AVG_R_WINDOW,
    avg_r_consecutive: int = AVG_R_CONSECUTIVE,
    slippage_window: int = SLIPPAGE_WINDOW,
    slippage_ratio: float = SLIPPAGE_RATIO,
) -> Dict[str, Any]:
    """
    Check a strategy for decay signals.

    Returns:
        {healthy: bool, trigger: str or None, metrics: {...}}
    """
    if not trades:
        return {
            "healthy": True,
            "trigger": None,
            "metrics": {
                "trailing_pf": None,
                "avg_r_windows": [],
                "slippage_violations": 0,
            },
        }

    # ── 1. Trailing profit factor ───────────────────────────────────────────
    trailing = trades[-pf_window:] if len(trades) >= pf_window else trades
    gross_profit = sum(t["pnl"] for t in trailing if t.get("pnl", 0) > 0)
    gross_loss = abs(sum(t["pnl"] for t in trailing if t.get("pnl", 0) < 0))
    trailing_pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    if len(trades) >= pf_window and trailing_pf < PF_THRESHOLD:
        return {
            "healthy": False,
            "trigger": f"trailing-{pf_window}-trade PF {trailing_pf:.3f} < {PF_THRESHOLD}",
            "metrics": {
                "trailing_pf": round(trailing_pf, 4),
                "avg_r_windows": [],
                "slippage_violations": 0,
            },
        }

    # ── 2. Consecutive negative avg-R windows ────────────────────────────────
    avg_r_values = _compute_avg_r_windows(trades, avg_r_window)
    negative_streak = 0
    for avg_r in avg_r_values:
        if avg_r < AVG_R_THRESHOLD:
            negative_streak += 1
            if negative_streak >= avg_r_consecutive:
                return {
                    "healthy": False,
                    "trigger": f"trailing-{avg_r_window}-trade avg R < 0 for {avg_r_consecutive} consecutive windows",
                    "metrics": {
                        "trailing_pf": round(trailing_pf, 4) if trailing_pf != float("inf") else "inf",
                        "avg_r_windows": [round(r, 4) for r in avg_r_values],
                        "slippage_violations": 0,
                    },
                }
        else:
            negative_streak = 0

    # ── 3. Slippage decay ───────────────────────────────────────────────────
    # Realised slippage > 2x modelled for `slippage_window` consecutive trades
    if len(trades) >= slippage_window:
        recent = trades[-slippage_window:]
        violations = 0
        max_violations = 0
        for t in recent:
            realised = abs(float(t.get("realised_slippage", 0)))
            modelled = abs(float(t.get("modelled_slippage", 0)))
            if modelled > 0 and realised > modelled * slippage_ratio:
                violations += 1
                max_violations = max(max_violations, violations)
            else:
                violations = 0

        if max_violations >= slippage_window:
            return {
                "healthy": False,
                "trigger": f"realised slippage > {slippage_ratio}x modelled for {slippage_window} consecutive trades",
                "metrics": {
                    "trailing_pf": round(trailing_pf, 4) if trailing_pf != float("inf") else "inf",
                    "avg_r_windows": [round(r, 4) for r in avg_r_values],
                    "slippage_violations": max_violations,
                },
            }

    return {
        "healthy": True,
        "trigger": None,
        "metrics": {
            "trailing_pf": round(trailing_pf, 4) if trailing_pf != float("inf") else "inf",
            "avg_r_windows": [round(r, 4) for r in avg_r_values],
            "slippage_violations": 0,
        },
    }


def _compute_avg_r_windows(
    trades: List[Dict[str, Any]],
    window: int,
) -> List[float]:
    """Split trades into non-overlapping windows and compute avg R each."""
    results = []
    i = len(trades) - window
    while i >= 0:
        chunk = trades[i : i + window]
        avg_r = sum(t.get("R", 0.0) for t in chunk) / len(chunk) if chunk else 0.0
        results.append(avg_r)
        i -= window
    # Return in chronological order
    results.reverse()
    return results


def watch_all(
    trades_csv_path: str,
    active_strategies: List[str],
    pf_window: int = PF_WINDOW,
    avg_r_window: int = AVG_R_WINDOW,
    avg_r_consecutive: int = AVG_R_CONSECUTIVE,
    slippage_window: int = SLIPPAGE_WINDOW,
    slippage_ratio: float = SLIPPAGE_RATIO,
) -> Dict[str, Any]:
    """
    Run check_decay on every active strategy.

    Args:
        trades_csv_path: path to CSV with columns (strategy_id, ticker, pnl, R,
                         realised_slippage, modelled_slippage, timestamp)
        active_strategies: list of strategy IDs to check

    Returns:
        {actions: [{strategy_id, trigger, metrics, action}], summary: str}
    """
    # Read trades from CSV
    all_trades: Dict[str, List[Dict[str, Any]]] = {sid: [] for sid in active_strategies}

    try:
        with open(trades_csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get("strategy_id", "")
                if sid in all_trades:
                    all_trades[sid].append({
                        "pnl": float(row.get("pnl", 0)),
                        "R": float(row.get("R", 0)),
                        "realised_slippage": float(row.get("realised_slippage", 0)),
                        "modelled_slippage": float(row.get("modelled_slippage", 0)),
                        "ticker": row.get("ticker", ""),
                    })
    except FileNotFoundError:
        pass

    actions = []
    for sid in active_strategies:
        result = check_decay(
            sid, all_trades.get(sid, []),
            pf_window=pf_window,
            avg_r_window=avg_r_window,
            avg_r_consecutive=avg_r_consecutive,
            slippage_window=slippage_window,
            slippage_ratio=slippage_ratio,
        )
        if not result["healthy"]:
            actions.append({
                "strategy_id": sid,
                "trigger": result["trigger"],
                "metrics": result["metrics"],
                "action": "auto_demote",
            })

    return {
        "actions": actions,
        "summary": f"{len(actions)} strategy(s) need demotion out of {len(active_strategies)} active",
    }


def auto_demote(strategy_id: str, reason: str) -> Dict[str, Any]:
    """
    Move strategy note from Active/ to Hypotheses/ and open a review note.

    In a real system this would move Obsidian notes and create review files.
    For now, returns an action record that callers can use.
    """
    return {
        "strategy_id": strategy_id,
        "action": "auto_demote",
        "reason": reason,
        "from_status": "Active",
        "to_status": "Hypotheses",
        "review_required": True,
        "review_note": f"Auto-demoted {strategy_id}: {reason}. Manual review required to reactivate.",
    }