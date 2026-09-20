#!/usr/bin/env python3
"""
G7 Live Forward Performance Gate

US-147: Formalizes live paper-trading performance as the G7 gate.
Wraps live_performance_tracker.py (US-112) with pass/fail criteria.

G7 PASS conditions (all must be true):
  1. At least MIN_LIVE_TRADES live trades executed
  2. Live win rate within ±1.5σ of backtest expected win rate
  3. Live avg R within ±1.5σ of backtest expected avg R
  4. No divergence >2σ in the last 20 live trades
  5. Strategy produced at least 1 signal in the last 7 calendar days (alive check)

Usage:
    python3 g7_live_forward.py                            # all active strategies
    python3 g7_live_forward.py --strategy STR-Q-stocks    # single strategy
    python3 g7_live_forward.py --json                     # JSON output
"""

import sys
import json
import csv
import argparse
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "paper_trading"))

# ── Gate thresholds ──────────────────────────────────────────────────
MIN_LIVE_TRADES = 10           # minimum sample for statistical comparison
SIGMA_WINDOW = 1.5             # ±sigma tolerance for win rate and avg R
DIVERGENCE_SIGMA = 2.0         # instant-fail if any metric exceeds this
RECENT_WINDOW = 20             # lookback for recent-divergence check
STALE_DAYS = 7                 # days without a signal = strategy is dormant

# ── Backtest expectations (mirrors live_performance_tracker.py) ──────
BACKTEST_EXPECTATIONS = {
    "STR-Q-stocks":           {"win_rate": 0.47,  "avg_r": 0.67,  "std_r": 2.1},
    "STR-Q-crypto":           {"win_rate": 0.40,  "avg_r": -1.02, "std_r": 2.8},
    "STR-B-macd-divergence":  {"win_rate": 0.44,  "avg_r": 0.86,  "std_r": 2.3},
    "STR-A-ma-pullback":      {"win_rate": 0.51,  "avg_r": 0.52,  "std_r": 1.9},
    "STR-VIXC-contango":      {"win_rate": 0.46,  "avg_r": 0.09,  "std_r": 1.5},
    "STR-LOWCORR-regime":     {"win_rate": 0.48,  "avg_r": 0.08,  "std_r": 1.4},
    "STR-OILSHOCK-rotation":  {"win_rate": 0.55,  "avg_r": 0.35,  "std_r": 2.0},
}

TRADES_LOG = Path("/root/HermesForge/scripts/paper_trading/trades_log.csv")


@dataclass
class G7Verdict:
    strategy_id: str
    passed: bool
    live_trades: int = 0
    live_win_rate: float = 0.0
    live_avg_r: float = 0.0
    expected_win_rate: float = 0.0
    expected_avg_r: float = 0.0
    wr_sigma: float = 0.0
    r_sigma: float = 0.0
    recent_divergence: bool = False
    last_signal_days: Optional[int] = None
    failures: list = field(default_factory=list)


def load_live_trades(strategy_id: Optional[str] = None) -> list[dict]:
    """Load closed trades from trades_log.csv."""
    if not TRADES_LOG.exists():
        return []
    trades = []
    with open(TRADES_LOG, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("status") == "closed":
                if strategy_id and row.get("strategy_id") != strategy_id:
                    continue
                trades.append(row)
    return trades


def compute_live_stats(trades: list[dict]) -> dict:
    """Compute live win rate, avg R, and recent divergence."""
    if not trades:
        return {"count": 0, "win_rate": 0, "avg_r": 0, "std_r": 0,
                "recent_avg_r": 0, "last_date": None}

    r_values = []
    wins = 0
    for t in trades:
        try:
            r = float(t.get("r_multiple", 0))
            r_values.append(r)
            if r > 0:
                wins += 1
        except (ValueError, TypeError):
            pass

    count = len(r_values)
    win_rate = wins / count if count else 0
    avg_r = sum(r_values) / count if count else 0

    # Standard deviation
    if count > 1:
        variance = sum((r - avg_r) ** 2 for r in r_values) / (count - 1)
        std_r = math.sqrt(variance)
    else:
        std_r = 0

    # Recent window
    recent = r_values[-RECENT_WINDOW:] if count >= RECENT_WINDOW else r_values
    recent_avg_r = sum(recent) / len(recent) if recent else 0

    # Last trade date
    last_date = None
    if trades:
        latest = max(trades, key=lambda t: t.get("exit_date", ""))
        last_date = latest.get("exit_date", None)

    return {
        "count": count,
        "win_rate": win_rate,
        "avg_r": avg_r,
        "std_r": std_r,
        "recent_avg_r": recent_avg_r,
        "last_date": last_date,
    }


def check_g7(strategy_id: str, live_stats: dict,
             expectations: Optional[dict] = None) -> G7Verdict:
    """Run G7 pass/fail checks."""
    if expectations is None:
        expectations = BACKTEST_EXPECTATIONS.get(strategy_id, {})
    if not expectations:
        return G7Verdict(strategy_id=strategy_id, passed=False,
                         failures=["No backtest expectations defined"])

    exp_wr = expectations.get("win_rate", 0.5)
    exp_r = expectations.get("avg_r", 0)
    exp_std = expectations.get("std_r", 2.0)

    live_count = live_stats["count"]
    live_wr = live_stats["win_rate"]
    live_avg = live_stats["avg_r"]
    live_std = live_stats.get("std_r", 0.0)
    recent_avg = live_stats.get("recent_avg_r", 0.0)

    failures = []

    # 1. Minimum trades
    if live_count < MIN_LIVE_TRADES:
        failures.append(f"insufficient trades: {live_count}/{MIN_LIVE_TRADES}")

    # 2. Win rate check
    if live_count >= MIN_LIVE_TRADES:
        wr_se = exp_std / math.sqrt(live_count) if live_count > 0 else 999
        wr_diff = abs(live_wr - exp_wr)
        wr_sigma = wr_diff / wr_se if wr_se > 0 else 0

        if wr_sigma > DIVERGENCE_SIGMA:
            failures.append(f"win rate divergence >2σ: live={live_wr:.1%} exp={exp_wr:.1%} σ={wr_sigma:.1f}")
        elif wr_sigma > SIGMA_WINDOW:
            failures.append(f"win rate outside {SIGMA_WINDOW}σ: live={live_wr:.1%} exp={exp_wr:.1%} σ={wr_sigma:.1f}")
    else:
        wr_sigma = 0

    # 3. Avg R check
    if live_count >= MIN_LIVE_TRADES:
        r_se = live_std / math.sqrt(live_count) if live_count > 0 else 999
        r_diff = abs(live_avg - exp_r)
        r_sigma = r_diff / r_se if r_se > 0 else 0

        if r_sigma > DIVERGENCE_SIGMA:
            failures.append(f"avg R divergence >2σ: live={live_avg:.2f} exp={exp_r:.2f} σ={r_sigma:.1f}")
        elif r_sigma > SIGMA_WINDOW:
            failures.append(f"avg R outside {SIGMA_WINDOW}σ: live={live_avg:.2f} exp={exp_r:.2f} σ={r_sigma:.1f}")
    else:
        r_sigma = 0

    # 4. Recent divergence
    if live_count >= RECENT_WINDOW:
        recent_diff = abs(recent_avg - exp_r)
        recent_se = live_std / math.sqrt(RECENT_WINDOW) if live_std > 0 else 999
        if recent_se > 0 and recent_diff / recent_se > DIVERGENCE_SIGMA:
            failures.append(f"recent divergence: last {RECENT_WINDOW} avg R={recent_avg:.2f} vs exp={exp_r:.2f}")
            recent_divergence = True
        else:
            recent_divergence = False
    else:
        recent_divergence = False

    # 5. Staleness check
    last_signal_days = None
    if live_stats.get("last_date"):
        try:
            last_dt = datetime.fromisoformat(str(live_stats["last_date"]).replace("Z", "+00:00"))
            delta = (datetime.now(timezone.utc) - last_dt).days
            last_signal_days = delta
            if delta > STALE_DAYS:
                failures.append(f"strategy dormant: {delta} days since last trade")
        except (ValueError, TypeError):
            pass

    passed = len(failures) == 0
    return G7Verdict(
        strategy_id=strategy_id,
        passed=passed,
        live_trades=live_count,
        live_win_rate=live_wr,
        live_avg_r=live_avg,
        expected_win_rate=exp_wr,
        expected_avg_r=exp_r,
        wr_sigma=wr_sigma,
        r_sigma=r_sigma,
        recent_divergence=recent_divergence,
        last_signal_days=last_signal_days,
        failures=failures,
    )


def check_all_active() -> dict[str, G7Verdict]:
    """Run G7 on all strategies with backtest expectations."""
    all_trades = load_live_trades()
    results = {}

    for strategy_id in BACKTEST_EXPECTATIONS:
        strategy_trades = [t for t in all_trades if t.get("strategy_id") == strategy_id]
        live_stats = compute_live_stats(strategy_trades)
        verdict = check_g7(strategy_id, live_stats)
        results[strategy_id] = verdict

    return results


def format_report(results: dict[str, G7Verdict]) -> str:
    """Human-readable G7 report."""
    lines = ["# G7 Live Forward Performance", "",
             f"Min trades: {MIN_LIVE_TRADES}, Sigma window: ±{SIGMA_WINDOW}σ, "
             f"Divergence fail: >{DIVERGENCE_SIGMA}σ",
             ""]

    passed = [v for v in results.values() if v.passed]
    failed = [v for v in results.values() if not v.passed]

    lines.append(f"**PASS:** {len(passed)}  |  **FAIL:** {len(failed)}")
    lines.append("")

    for name, verdicts in [("❌ FAILED", failed), ("✅ PASSED", passed)]:
        if not verdicts:
            continue
        lines.append(f"## {name} ({len(verdicts)})")
        for v in verdicts:
            lines.append(f"### {v.strategy_id}")
            lines.append(f"- Trades: {v.live_trades}")
            lines.append(f"- Win rate: {v.live_win_rate:.1%} live vs {v.expected_win_rate:.1%} expected ({v.wr_sigma:.1f}σ)")
            lines.append(f"- Avg R: {v.live_avg_r:.2f} live vs {v.expected_avg_r:.2f} expected ({v.r_sigma:.1f}σ)")
            if v.last_signal_days is not None:
                lines.append(f"- Last signal: {v.last_signal_days}d ago")
            if v.failures:
                for f in v.failures:
                    lines.append(f"- ⚠ {f}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="G7 Live Forward Performance Gate")
    parser.add_argument("--strategy", help="Single strategy ID to check")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.strategy:
        trades = load_live_trades(args.strategy)
        live_stats = compute_live_stats(trades)
        verdict = check_g7(args.strategy, live_stats)
        results = {args.strategy: verdict}
    else:
        results = check_all_active()

    if args.json:
        output = {}
        for sid, v in results.items():
            output[sid] = {
                "passed": v.passed,
                "live_trades": v.live_trades,
                "live_win_rate": v.live_win_rate,
                "live_avg_r": v.live_avg_r,
                "expected_win_rate": v.expected_win_rate,
                "expected_avg_r": v.expected_avg_r,
                "wr_sigma": round(v.wr_sigma, 2),
                "r_sigma": round(v.r_sigma, 2),
                "recent_divergence": v.recent_divergence,
                "last_signal_days": v.last_signal_days,
                "failures": v.failures,
            }
        print(json.dumps(output, indent=2))
    else:
        print(format_report(results))


if __name__ == "__main__":
    main()