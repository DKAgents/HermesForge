#!/usr/bin/env python3
"""
backfill_hostile_r.py — US-224: persist the authoritative bar-level hostile_r
onto trades.csv.

Reads the two hostile-fill ledgers (STR-Q on signal_id, six swing strategies on
trade_id), resolves the AUTHORITATIVE fill-realistic R exactly as
performance_report does (closed stage, non-null hostile_r, latest timestamp
wins), and writes it into trades.csv's `hostile_r` column.

Safety (US-224 hard rules):
  - NON-DESTRUCTIVE: row count is preserved exactly; `_write_all_rows` refuses
    a >20% drop and uses an atomic temp→rename.
  - `outlier_excluded` rows are left EMPTY (never written as a false R).
  - Trades with no resolvable hostile_r (skip/open stage, not in ledger) stay
    empty and fall back to the jsonls at read time.

Usage:
    python3 backfill_hostile_r.py            # backfill (idempotent)
    python3 backfill_hostile_r.py --dry-run  # report what would change, no write
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import trade_log
import performance_report as pr


def authoritative_maps():
    """Return (strq_map, swing_map) of authoritative closed-stage hostile rows.

    Reuses performance_report's canonical loader so the backfill value is, by
    construction, identical to what the report would compute from the jsonls.
    """
    strq_map = pr._load_hostile_ledger(pr.STRQ_LEDGER, "signal_id")
    swing_map = pr._load_hostile_ledger(pr.SWING_LEDGER, "trade_id")
    return strq_map, swing_map


def resolve(rows):
    """Backfill hostile_r onto `rows` in place. Returns (filled, outliers).

    `rows` is a list of dicts from trade_log._read_all_rows(). A row is matched
    to the STR-Q ledger on signal_id, or the swing ledger on trade_id (per the
    same _join_key logic the report uses). outlier_excluded rows are left empty.
    """
    strq_map, swing_map = authoritative_maps()
    filled = 0
    outliers = 0
    for row in rows:
        sid = row.get("strategy_id", "")
        key = pr._join_key(sid, row)
        hr_row = None
        if sid == pr.STR_Q_STRATEGY:
            hr_row = strq_map.get(key)
        elif sid in pr.SWING_STRATEGIES:
            hr_row = swing_map.get(key)
        if hr_row is None:
            continue
        if hr_row.get("outlier_excluded"):
            outliers += 1
            continue
        row["hostile_r"] = hr_row.get("hostile_r", "")
        filled += 1
    return filled, outliers


def main():
    dry_run = "--dry-run" in sys.argv
    rows = trade_log._read_all_rows()
    filled, outliers = resolve(rows)

    print(f"{'='*60}")
    print(f"backfill_hostile_r (US-224)")
    print(f"  trades.csv rows:       {len(rows)}")
    print(f"  hostile_r backfilled:  {filled}")
    print(f"  outlier_excluded left empty: {outliers}")

    if dry_run:
        print(f"  (dry-run — nothing written to trades.csv)")
        return

    trade_log._write_all_rows(rows)
    print(f"  wrote hostile_r column to {trade_log.LOG_PATH}")


if __name__ == "__main__":
    main()