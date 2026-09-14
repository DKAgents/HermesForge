#!/usr/bin/env python3
"""
backfill_trials.py — Read all CSV backtest results and create trial ledger entries.

Run: python3 backfill_trials.py
Reads from: /root/HermesForge/scripts/validation/results/*.csv
Writes to:  /root/HermesForge/data/gauntlet/trials.jsonl
"""

import csv
import hashlib
import os
import sys
from pathlib import Path

# Add parent to path for trials_ledger import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from trials_ledger import increment_trial, count, verify_integrity

RESULTS_DIR = Path("/root/HermesForge/scripts/validation/results")


def _sha256_file(path: Path) -> str:
    """SHA256 hash of file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _count_trades(csv_path: Path) -> int:
    """Count non-header, non-empty lines in CSV."""
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        return sum(1 for row in reader if any(cell.strip() for cell in row))


def _parse_date_range(rows: list[dict]) -> tuple[str, str]:
    """Extract period_start / period_end from row dates."""
    dates = []
    date_cols = ["date", "Date", "timestamp", "entry_date"]
    for row in rows:
        for col in date_cols:
            val = row.get(col, "")
            if val:
                dates.append(val.split(" ")[0])  # strip time if present
                break
    if not dates:
        return ("unknown", "unknown")
    dates.sort()
    return (dates[0], dates[-1])


def _compute_results(rows: list[dict], trade_count: int) -> dict:
    """Compute sharpe, avg_r, pf, trade_count from r_multiple column or fallbacks."""
    result: dict = {
        "trade_count": trade_count,
        "sharpe": 0.0,
        "avg_r": 0.0,
        "pf": 0.0,
        "r_outliers_skipped": 0,
    }

    r_vals = []
    r_skipped = 0

    # Check if this CSV has an equity curve (no trade-level data)
    has_equity = any("equity" in (k or "").lower() for k in rows[0].keys()) if rows else False
    has_trades = any(k in rows[0] for k in ("entry_price", "exit_price"))

    if has_equity and not has_trades and "r_multiple" not in rows[0]:
        # Equity curve — compute returns from equity column
        eq_key = next((k for k in rows[0] if "equity" in (k or "").lower()), None)
        if eq_key:
            eq_vals = []
            for row in rows:
                try:
                    eq_vals.append(float(row[eq_key]))
                except (ValueError, TypeError):
                    continue
            if len(eq_vals) > 1:
                returns = [
                    (eq_vals[i] - eq_vals[i - 1]) / max(abs(eq_vals[i - 1]), 1e-9)
                    for i in range(1, len(eq_vals))
                ]
                returns = [r for r in returns if abs(r) < 10]  # cap single-period return
                if returns:
                    mean_ret = sum(returns) / len(returns)
                    variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1) if len(returns) > 1 else 0
                    std_ret = variance**0.5
                    result["sharpe"] = round(mean_ret / std_ret, 6) if std_ret > 0 else 0.0
                    result["avg_r"] = round(mean_ret, 6)
                    result["pf"] = 1.0
            return result

    # Standard path: try r_multiple first, then compute from prices
    for row in rows:
        r_str = row.get("r_multiple", row.get("R_multiple", ""))
        if r_str:
            try:
                val = float(r_str)
            except (ValueError, TypeError):
                continue
            if abs(val) > 1000:
                r_skipped += 1
                continue
            r_vals.append(val)
        elif has_trades:
            # Compute approximate r_multiple from entry/exit
            try:
                entry = float(row.get("entry_price", 0))
                exit_p = float(row.get("exit_price", 0))
                if entry and entry != 0:
                    val = (exit_p - entry) / entry
                    if abs(val) <= 1000:
                        r_vals.append(val)
                    else:
                        r_skipped += 1
            except (ValueError, TypeError):
                continue

    result["r_outliers_skipped"] = r_skipped

    if not r_vals:
        return result

    result["avg_r"] = round(sum(r_vals) / len(r_vals), 6)

    # Sharpe: mean / std of R-multiples (assuming risk-free = 0)
    if len(r_vals) > 1:
        mean_r = sum(r_vals) / len(r_vals)
        variance = sum((r - mean_r) ** 2 for r in r_vals) / (len(r_vals) - 1)
        std_r = variance**0.5
        result["sharpe"] = round(mean_r / std_r, 6) if std_r > 0 else 0.0

    # Profit factor: gross_profit / gross_loss
    gains = sum(r for r in r_vals if r > 0)
    losses = abs(sum(r for r in r_vals if r < 0))
    result["pf"] = round(gains / losses, 6) if losses > 0 else (999.0 if gains > 0 else 0.0)

    # Additional stats
    result["win_rate"] = round(sum(1 for r in r_vals if r > 0) / len(r_vals), 6) if r_vals else 0.0
    result["max_r"] = round(max(r_vals), 6)
    result["min_r"] = round(min(r_vals), 6)

    return result


def _read_csv_rows(path: Path) -> list[dict]:
    """Read all rows from a CSV as dicts."""
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if any(v.strip() for v in row.values()):
                rows.append(row)
    return rows


def backfill() -> dict:
    """
    Backfill all CSVs into the trials ledger.
    Returns a summary dict: {total, succeeded, failed, errors: [...]}
    """
    csv_files = sorted(RESULTS_DIR.glob("*.csv"))
    summary = {"total": len(csv_files), "succeeded": 0, "failed": 0, "errors": []}

    for csv_path in csv_files:
        hypothesis_id = csv_path.stem
        try:
            rows = _read_csv_rows(csv_path)
            if not rows:
                summary["failed"] += 1
                summary["errors"].append(f"{hypothesis_id}: no data rows")
                continue

            trade_count = len(rows)
            period_start, period_end = _parse_date_range(rows)
            results = _compute_results(rows, trade_count)

            # param_hash = hash of CSV contents
            param_hash = _sha256_file(csv_path)
            # universe_hash derived from symbols/tickers in the CSV
            symbols = set()
            sym_cols = ["symbol", "ticker", "Symbol", "Ticker"]
            for row in rows:
                for col in sym_cols:
                    val = row.get(col, "")
                    if val:
                        symbols.add(val.strip())
                        break
            universe_str = ",".join(sorted(symbols))
            universe_hash = hashlib.sha256(universe_str.encode()).hexdigest()

            increment_trial(
                hypothesis_id=hypothesis_id,
                param_hash=param_hash,
                universe_hash=universe_hash,
                period_start=period_start,
                period_end=period_end,
                result=results,
            )
            summary["succeeded"] += 1
        except Exception as e:
            summary["failed"] += 1
            summary["errors"].append(f"{hypothesis_id}: {e}")

    return summary


if __name__ == "__main__":
    # Clear existing ledger for clean backfill
    ledger_path = Path("/root/HermesForge/data/gauntlet/trials.jsonl")
    if ledger_path.exists():
        ledger_path.unlink()

    print(f"Backfilling {len(sorted(RESULTS_DIR.glob('*.csv')))} CSV files...")
    summary = backfill()

    print(f"\n{'='*60}")
    print(f"Backfill complete.")
    print(f"  Total CSVs:     {summary['total']}")
    print(f"  Succeeded:      {summary['succeeded']}")
    print(f"  Failed:         {summary['failed']}")
    print(f"  Ledger count:   {count()}")

    if summary["errors"]:
        print(f"\nErrors:")
        for err in summary["errors"]:
            print(f"  - {err}")

    valid, msg = verify_integrity()
    print(f"\nHash chain:      {'VALID' if valid else 'BROKEN'} — {msg}")