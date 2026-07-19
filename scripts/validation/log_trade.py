#!/usr/bin/env python3
"""
log_trade.py — Paper trade logger for HermesForge validation.

Usage:
  python3 log_trade.py --strategy b --ticker AAPL --direction long \
      --entry 185.50 --stop 183.20 --target 192.00 --exit 191.50 \
      --exit_reason target --bars_held 5 --confirmation_level 2 \
      --weekly_gates 2 --trigger_type macd_cross --notes "clean setup"

Add --dry-run to preview without saving.
"""

import argparse
import csv
import os
import sys
from datetime import date, datetime

# ── Constants ────────────────────────────────────────────────────────────────

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "paper_trades.csv")

STRATEGY_MAP = {
    "a": "STR-A-ma-pullback-fibonacci",
    "b": "STR-B-macd-histogram-divergence",
    "c": "STR-C-breakout-volume",
    "d": "STR-D-sr-role-reversal",
}

CSV_COLUMNS = [
    "trade_id", "strategy_id", "ticker", "direction",
    "entry_date", "entry_price", "stop_price", "target_price",
    "exit_date", "exit_price", "exit_reason", "r_multiple",
    "bars_held", "subperiod", "confirmation_level",
    "weekly_gates_passing", "trigger_type", "notes",
]

MAX_PORTFOLIO_HEAT = 5      # percent
RISK_PER_TRADE     = 1      # percent (assumed flat)

# ── Helpers ──────────────────────────────────────────────────────────────────

def assign_subperiod(entry_date: date) -> str:
    """Return sub-period label based on entry date."""
    if date(2019, 4, 1) <= entry_date <= date(2021, 12, 31):
        return "period1_bull"
    elif date(2022, 1, 1) <= entry_date <= date(2023, 12, 31):
        return "period2_bear"
    elif entry_date >= date(2024, 1, 1):
        return "period3_current"
    else:
        return "period0_pre"


def compute_r_multiple(direction: str, entry: float, stop: float, exit_price: float) -> float:
    """
    R-multiple:
      long  → (exit − entry) / (entry − stop)
      short → (entry − exit) / (stop − entry)
    """
    if direction == "long":
        risk = entry - stop
        reward = exit_price - entry
    else:  # short
        risk = stop - entry
        reward = entry - exit_price

    if risk <= 0:
        raise ValueError(
            f"Invalid risk: entry={entry}, stop={stop}, direction={direction}. "
            "For long trades entry must be > stop; for short trades stop must be > entry."
        )
    return round(reward / risk, 3)


def read_trades() -> list[dict]:
    """Return all existing rows from the CSV as a list of dicts."""
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def count_open_trades(trades: list[dict]) -> int:
    """Rows with no exit_date are counted as open positions."""
    return sum(1 for t in trades if not t.get("exit_date", "").strip())


def next_trade_id(trades: list[dict]) -> str:
    return f"TRADE-{len(trades) + 1:03d}"


def running_stats(trades: list[dict]) -> dict:
    """Compute overall stats across all trades that have an exit."""
    closed = [t for t in trades if t.get("exit_date", "").strip()]
    total  = len(closed)
    if total == 0:
        return {"total": 0, "win_rate": 0.0, "avg_r": 0.0}
    r_vals   = [float(t["r_multiple"]) for t in closed]
    wins     = sum(1 for r in r_vals if r > 0)
    win_rate = round(wins / total * 100, 1)
    avg_r    = round(sum(r_vals) / total, 3)
    return {"total": total, "win_rate": win_rate, "avg_r": avg_r}


def format_row(
    trade_id: str,
    strategy_id: str,
    ticker: str,
    direction: str,
    entry_date: str,
    entry_price: float,
    stop_price: float,
    target_price: float,
    exit_price: float,
    exit_reason: str,
    r_multiple: float,
    bars_held: int,
    subperiod: str,
    confirmation_level: int,
    weekly_gates: int,
    trigger_type: str,
    notes: str,
) -> dict:
    return {
        "trade_id":            trade_id,
        "strategy_id":         strategy_id,
        "ticker":              ticker.upper(),
        "direction":           direction,
        "entry_date":          entry_date,
        "entry_price":         entry_price,
        "stop_price":          stop_price,
        "target_price":        target_price,
        "exit_date":           entry_date,   # same-session exit; pass '' if still open
        "exit_price":          exit_price,
        "exit_reason":         exit_reason,
        "r_multiple":          r_multiple,
        "bars_held":           bars_held,
        "subperiod":           subperiod,
        "confirmation_level":  confirmation_level,
        "weekly_gates_passing": weekly_gates,
        "trigger_type":        trigger_type,
        "notes":               notes,
    }


def append_trade(row: dict) -> None:
    """Append a single trade row to the CSV."""
    file_exists = os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        if not file_exists or os.path.getsize(CSV_PATH) == 0:
            writer.writeheader()
        writer.writerow(row)


# ── CLI ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Log a paper trade to HermesForge paper_trades.csv",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--strategy",          required=True,
                   choices=["a", "b", "c", "d"],
                   help="Strategy key: a/b/c/d")
    p.add_argument("--ticker",            required=True,  help="Ticker symbol, e.g. AAPL")
    p.add_argument("--direction",         required=True,  choices=["long", "short"])
    p.add_argument("--entry",             required=True,  type=float, help="Entry price")
    p.add_argument("--stop",              required=True,  type=float, help="Stop price")
    p.add_argument("--target",            required=True,  type=float, help="Target price")
    p.add_argument("--exit",              required=True,  type=float, help="Exit price",
                   dest="exit_price")
    p.add_argument("--exit_reason",       required=True,
                   help="Reason for exit (e.g. target, stop, manual)")
    p.add_argument("--bars_held",         required=True,  type=int,
                   help="Number of bars held")
    p.add_argument("--confirmation_level",required=True,  type=int,
                   choices=[1, 2, 3],
                   help="Confirmation level 1-3")
    p.add_argument("--weekly_gates",      required=True,  type=int,
                   help="Number of weekly gates passing (0-3)")
    p.add_argument("--trigger_type",      required=True,
                   help="Entry trigger type, e.g. macd_cross")
    p.add_argument("--notes",             default="",     help="Optional free-text notes")
    p.add_argument("--dry-run",           action="store_true",
                   help="Preview the trade row without saving to CSV")
    return p


def main() -> None:
    args = build_parser().parse_args()

    # ── Resolve derived fields ────────────────────────────────────────────────
    strategy_id  = STRATEGY_MAP[args.strategy]
    today        = date.today()
    entry_date   = today.isoformat()
    subperiod    = assign_subperiod(today)

    try:
        r_multiple = compute_r_multiple(
            args.direction, args.entry, args.stop, args.exit_price
        )
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    # ── Read existing trades ──────────────────────────────────────────────────
    existing    = read_trades()
    trade_id    = next_trade_id(existing)
    open_count  = count_open_trades(existing)

    # ── Portfolio heat check ──────────────────────────────────────────────────
    projected_heat = (open_count + 1) * RISK_PER_TRADE
    if projected_heat > MAX_PORTFOLIO_HEAT:
        print(
            f"[WARNING] Portfolio heat check: {open_count} currently open trade(s) "
            f"+ this trade = {projected_heat}% risk, which exceeds the "
            f"{MAX_PORTFOLIO_HEAT}% limit. Proceed with caution.",
            file=sys.stderr,
        )

    # ── Build row ─────────────────────────────────────────────────────────────
    row = format_row(
        trade_id           = trade_id,
        strategy_id        = strategy_id,
        ticker             = args.ticker,
        direction          = args.direction,
        entry_date         = entry_date,
        entry_price        = args.entry,
        stop_price         = args.stop,
        target_price       = args.target,
        exit_price         = args.exit_price,
        exit_reason        = args.exit_reason,
        r_multiple         = r_multiple,
        bars_held          = args.bars_held,
        subperiod          = subperiod,
        confirmation_level = args.confirmation_level,
        weekly_gates       = args.weekly_gates,
        trigger_type       = args.trigger_type,
        notes              = args.notes,
    )

    # ── Dry-run output ────────────────────────────────────────────────────────
    if args.dry_run:
        print("\n[DRY-RUN] Trade row that would be logged:")
        print("-" * 54)
        for k, v in row.items():
            print(f"  {k:<24} {v}")
        print("-" * 54)
        print(f"\n  R-multiple : {r_multiple:+.3f}")
        print(f"  Sub-period : {subperiod}")
        print(f"  Trade ID   : {trade_id}")
        print("\n[DRY-RUN] No data written to CSV.\n")
        return

    # ── Save ──────────────────────────────────────────────────────────────────
    append_trade(row)

    # ── Stats (include the new trade) ─────────────────────────────────────────
    all_trades = existing + [row]
    stats      = running_stats(all_trades)

    print(f"\n✅  Trade logged successfully!")
    print(f"   Trade ID   : {trade_id}")
    print(f"   Ticker     : {args.ticker.upper()}  ({args.direction})")
    print(f"   Strategy   : {strategy_id}")
    print(f"   R-multiple : {r_multiple:+.3f}")
    print(f"   Sub-period : {subperiod}")
    print()
    print(f"📊  Running stats (closed trades):")
    print(f"   Total      : {stats['total']}")
    print(f"   Win rate   : {stats['win_rate']}%")
    print(f"   Avg R      : {stats['avg_r']:+.3f}")
    print(f"   CSV        : {CSV_PATH}\n")


if __name__ == "__main__":
    main()
