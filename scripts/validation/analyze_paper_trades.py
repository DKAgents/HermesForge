#!/usr/bin/env python3
"""
analyze_paper_trades.py — Summarise HermesForge paper trade results.

Usage:
  python3 analyze_paper_trades.py              # all strategies
  python3 analyze_paper_trades.py --strategy b  # filter to STR-B
"""

import argparse
import csv
import os
import statistics
import sys
from collections import defaultdict

# ── Constants ────────────────────────────────────────────────────────────────

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "paper_trades.csv")

STRATEGY_MAP = {
    "a": "STR-A-ma-pullback-fibonacci",
    "b": "STR-B-macd-histogram-divergence",
    "c": "STR-C-breakout-volume",
    "d": "STR-D-sr-role-reversal",
}

MIN_TRADES_FOR_STATS = 20

# ── Helpers ──────────────────────────────────────────────────────────────────

def read_trades(strategy_filter: str | None = None) -> list[dict]:
    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] CSV not found: {CSV_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(CSV_PATH, newline="") as fh:
        reader = csv.DictReader(fh)
        trades = list(reader)

    if strategy_filter:
        sid = STRATEGY_MAP.get(strategy_filter)
        if sid is None:
            print(f"[ERROR] Unknown strategy key '{strategy_filter}'. Use a/b/c/d.",
                  file=sys.stderr)
            sys.exit(1)
        trades = [t for t in trades if t.get("strategy_id") == sid]

    return trades


def closed_trades(trades: list[dict]) -> list[dict]:
    return [t for t in trades if t.get("exit_date", "").strip()]


def r_values(trades: list[dict]) -> list[float]:
    out = []
    for t in trades:
        try:
            out.append(float(t["r_multiple"]))
        except (ValueError, KeyError):
            pass
    return out


def win_rate(r_vals: list[float]) -> float:
    if not r_vals:
        return 0.0
    return round(sum(1 for r in r_vals if r > 0) / len(r_vals) * 100, 1)


def avg_r(r_vals: list[float]) -> float:
    return round(statistics.mean(r_vals), 3) if r_vals else 0.0


def median_r(r_vals: list[float]) -> float:
    return round(statistics.median(r_vals), 3) if r_vals else 0.0


def expected_value(r_vals: list[float]) -> float:
    """Simple EV: win_rate * avg_win + loss_rate * avg_loss."""
    if not r_vals:
        return 0.0
    wins   = [r for r in r_vals if r > 0]
    losses = [r for r in r_vals if r <= 0]
    wr     = len(wins) / len(r_vals)
    lr     = len(losses) / len(r_vals)
    aw     = statistics.mean(wins)   if wins   else 0.0
    al     = statistics.mean(losses) if losses else 0.0
    return round(wr * aw + lr * al, 3)


def hr(char: str = "─", width: int = 60) -> str:
    return char * width


# ── Display sections ─────────────────────────────────────────────────────────

def section_overall(trades: list[dict]) -> None:
    closed = closed_trades(trades)
    r_vals = r_values(closed)
    total  = len(trades)
    n_closed = len(closed)
    n_open   = total - n_closed

    print(hr("═"))
    print("  PAPER TRADE SUMMARY")
    print(hr("═"))
    print(f"  Total trades logged : {total}")
    print(f"  Closed              : {n_closed}")
    print(f"  Open (no exit)      : {n_open}")
    if total < MIN_TRADES_FOR_STATS:
        print(f"\n  ⚠️  WARNING: Only {total} trade(s) logged.")
        print(f"     Statistical results are unreliable until ≥{MIN_TRADES_FOR_STATS} trades.")

    if r_vals:
        print()
        print(f"  Win rate  : {win_rate(r_vals)}%")
        print(f"  Avg R     : {avg_r(r_vals):+.3f}")
        print(f"  Median R  : {median_r(r_vals):+.3f}")
        print(f"  EV (R)    : {expected_value(r_vals):+.3f}")
    else:
        print("\n  (No closed trades to compute stats.)")
    print()


def section_by_strategy(trades: list[dict]) -> None:
    print(hr())
    print("  BY STRATEGY")
    print(hr())
    by_strat: dict[str, list] = defaultdict(list)
    for t in closed_trades(trades):
        by_strat[t.get("strategy_id", "UNKNOWN")].append(float(t["r_multiple"]))

    if not by_strat:
        print("  (No closed trades.)\n")
        return

    col_w = [28, 7, 9, 9, 9, 9]
    header = (
        f"  {'Strategy':<{col_w[0]}} {'N':>{col_w[1]}} "
        f"{'Win%':>{col_w[2]}} {'Avg R':>{col_w[3]}} "
        f"{'Med R':>{col_w[4]}} {'EV':>{col_w[5]}}"
    )
    print(header)
    print("  " + "-" * (sum(col_w) + len(col_w) - 1))

    for strat, r_vals in sorted(by_strat.items()):
        wr_s  = f"{win_rate(r_vals):.1f}"
        ar_s  = f"{avg_r(r_vals):+.3f}"
        mr_s  = f"{median_r(r_vals):+.3f}"
        ev_s  = f"{expected_value(r_vals):+.3f}"
        print(
            f"  {strat:<{col_w[0]}} {len(r_vals):>{col_w[1]}} "
            f"{wr_s:>{col_w[2]}} {ar_s:>{col_w[3]}} "
            f"{mr_s:>{col_w[4]}} {ev_s:>{col_w[5]}}"
        )
    print()


def section_by_subperiod(trades: list[dict]) -> None:
    print(hr())
    print("  BY SUB-PERIOD")
    print(hr())
    by_period: dict[str, list] = defaultdict(list)
    for t in closed_trades(trades):
        by_period[t.get("subperiod", "unknown")].append(float(t["r_multiple"]))

    if not by_period:
        print("  (No closed trades.)\n")
        return

    col_w = [18, 7, 9, 9, 9]
    header = (
        f"  {'Sub-period':<{col_w[0]}} {'N':>{col_w[1]}} "
        f"{'Win%':>{col_w[2]}} {'Avg R':>{col_w[3]}} {'EV':>{col_w[4]}}"
    )
    print(header)
    print("  " + "-" * (sum(col_w) + len(col_w) - 1))

    for period, r_vals in sorted(by_period.items()):
        wr_s = f"{win_rate(r_vals):.1f}"
        ar_s = f"{avg_r(r_vals):+.3f}"
        ev_s = f"{expected_value(r_vals):+.3f}"
        print(
            f"  {period:<{col_w[0]}} {len(r_vals):>{col_w[1]}} "
            f"{wr_s:>{col_w[2]}} {ar_s:>{col_w[3]}} {ev_s:>{col_w[4]}}"
        )
    print()


def section_exit_reasons(trades: list[dict]) -> None:
    print(hr())
    print("  EXIT REASON BREAKDOWN")
    print(hr())
    by_reason: dict[str, list] = defaultdict(list)
    for t in closed_trades(trades):
        by_reason[t.get("exit_reason", "unknown")].append(float(t["r_multiple"]))

    if not by_reason:
        print("  (No closed trades.)\n")
        return

    col_w = [14, 7, 9, 9]
    header = (
        f"  {'Exit Reason':<{col_w[0]}} {'N':>{col_w[1]}} "
        f"{'Avg R':>{col_w[2]}} {'Win%':>{col_w[3]}}"
    )
    print(header)
    print("  " + "-" * (sum(col_w) + len(col_w) - 1))

    for reason, r_vals in sorted(by_reason.items()):
        ar_s = f"{avg_r(r_vals):+.3f}"
        wr_s = f"{win_rate(r_vals):.1f}"
        print(
            f"  {reason:<{col_w[0]}} {len(r_vals):>{col_w[1]}} "
            f"{ar_s:>{col_w[2]}} {wr_s:>{col_w[3]}}"
        )
    print()


def section_recent(trades: list[dict], n: int = 10) -> None:
    print(hr())
    print(f"  RECENT {n} TRADES (newest first)")
    print(hr())

    recent = list(reversed(trades[-n:])) if trades else []
    if not recent:
        print("  (No trades logged yet.)\n")
        return

    col_w = [10, 6, 6, 8, 7, 8, 9, 8]
    header = (
        f"  {'Trade ID':<{col_w[0]}} {'Ticker':<{col_w[1]}} "
        f"{'Dir':<{col_w[2]}} {'Entry':>{col_w[3]}} "
        f"{'Exit':>{col_w[4]}} {'R':>{col_w[5]}} "
        f"{'Reason':<{col_w[6]}} {'SubPeriod':<{col_w[7]}}"
    )
    print(header)
    print("  " + "-" * (sum(col_w) + len(col_w) - 1))

    for t in recent:
        r_str = f"{float(t['r_multiple']):+.2f}" if t.get("r_multiple") else "  open"
        print(
            f"  {t.get('trade_id','?'):<{col_w[0]}} "
            f"{t.get('ticker','?'):<{col_w[1]}} "
            f"{t.get('direction','?'):<{col_w[2]}} "
            f"{t.get('entry_price','?'):>{col_w[3]}} "
            f"{t.get('exit_price','?'):>{col_w[4]}} "
            f"{r_str:>{col_w[5]}} "
            f"{t.get('exit_reason','?'):<{col_w[6]}} "
            f"{t.get('subperiod','?'):<{col_w[7]}}"
        )
    print()
    print(hr("═"))
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Analyse HermesForge paper trade results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--strategy",
        choices=["a", "b", "c", "d"],
        default=None,
        help="Filter to a single strategy (a/b/c/d). Default: all.",
    )
    return p


def main() -> None:
    args   = build_parser().parse_args()
    trades = read_trades(strategy_filter=args.strategy)

    section_overall(trades)
    section_by_strategy(trades)
    section_by_subperiod(trades)
    section_exit_reasons(trades)
    section_recent(trades)


if __name__ == "__main__":
    main()
