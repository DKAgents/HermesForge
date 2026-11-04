#!/usr/bin/env python3
"""
backfill_swing_outlier_excluded.py — US-227 one-time field stamp.

Stamps `outlier_excluded` onto every EXISTING swing hostile ledger row WITHOUT
re-scoring hostile_r. A `--force` rescore (hostile_fills.py) re-runs the CURRENT
fill logic against drifted bar data and silently rewrites historical R — that is
unacceptable for the swing ledger, so this backfill mutates ONLY the new field.

For closed-stage rows the flag is computed EXACTLY as hostile_fills.py's gate:

    widened      = widen_stop(paper_entry, stop_price, direction, STOP_WIDEN_FACTOR)
    setup_risk   = abs(paper_entry - widened) / paper_entry
    outlier_excluded = setup_risk < DEGENERATE_RISK_FLOOR

Non-closed rows (entry/open/skip/skip_entry) are never scored, so the flag is
False. Idempotent: rows that already carry `outlier_excluded` are left untouched.
Reuses pnl_accounting constants (no duplication) and hostile_fills' atomic write
(a non-empty ledger is never wiped). Preserves row order and every other field.

Usage:
    python3 backfill_swing_outlier_excluded.py            # stamp (idempotent)
    python3 backfill_swing_outlier_excluded.py --dry-run  # report, no write
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import trade_log
import hostile_fills
from pnl_accounting import DEGENERATE_RISK_FLOOR, widen_stop, STOP_WIDEN_FACTOR


def _stop_lookup() -> dict:
    """Map signal_id -> trade_log row for swing trades (signal_id == trade_id)."""
    by_sig = {}
    for r in trade_log._read_all_rows():
        sig = (r.get("signal_id") or "").strip()
        if sig:
            by_sig[sig] = r
    return by_sig


def _compute_flag(row: dict, stop_lookup: dict) -> bool:
    """True when a closed row is a degenerate (near-zero-risk) stop. False otherwise."""
    if row.get("stage") != "closed":
        return False
    tr = stop_lookup.get(row.get("trade_id", ""))
    if tr is None:
        return False
    try:
        entry = float(row["paper_entry_price"])
        stop = float(tr["stop_price"])
    except (KeyError, TypeError, ValueError):
        return False
    if entry <= 0 or stop <= 0:
        return False
    widened = widen_stop(entry, stop, row.get("direction", ""), STOP_WIDEN_FACTOR)
    setup_risk = abs(entry - widened) / entry
    return setup_risk < DEGENERATE_RISK_FLOOR


def stamp(dry_run: bool = False) -> dict:
    """Stamp `outlier_excluded` on existing rows. Returns {stamped, outliers}."""
    path = hostile_fills.REPORT_PATH
    prev_count = sum(1 for _ in open(path)) if path.exists() else 0
    by_key = hostile_fills._load_existing(path)
    stop_lookup = _stop_lookup()

    stamped = 0
    outliers = 0
    for r in by_key.values():
        if "outlier_excluded" in r:
            continue
        o = _compute_flag(r, stop_lookup)
        r["outlier_excluded"] = o
        stamped += 1
        if o:
            outliers += 1

    if not dry_run:
        hostile_fills._write_atomic(by_key, path, prev_count)
    return {"stamped": stamped, "outliers": outliers, "total": len(by_key)}


def main():
    dry_run = "--dry-run" in sys.argv
    res = stamp(dry_run=dry_run)
    print(f"swing ledger rows:            {res['total']}")
    print(f"outlier_excluded stamped:     {res['stamped']}")
    print(f"degenerate (outlier) rows:    {res['outliers']}")
    if dry_run:
        print("  (dry-run — nothing written)")
    else:
        print(f"  wrote {hostile_fills.REPORT_PATH.name}")


if __name__ == "__main__":
    main()