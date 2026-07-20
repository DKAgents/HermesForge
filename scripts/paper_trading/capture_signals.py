#!/usr/bin/env python3
"""
capture_signals.py — HermesForge EPIC-010 (US-066)

Runs the daily scanners for strategies A, B, D (independent of Discord
publish_enabled flags -- paper trading has its own, lower bar) and
automatically opens a paper trade for every qualifying fresh signal.

Position sizing is currently a flat-1% stub pending US-067 (real sizing
matrix); the TODO below marks exactly what to swap in.

Usage:
    python3 capture_signals.py --dry-run     # show what would be opened
    python3 capture_signals.py               # actually opens trades
"""

import sys
import json
import argparse
import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))

from fetch_data import load_all  # noqa: E402
from scanners.scanner_a_ma_pullback import scan as scan_a       # noqa: E402
from scanners.scanner_b_macd_divergence import scan as scan_b   # noqa: E402
from scanners.scanner_d_sr_reversal import scan as scan_d       # noqa: E402

import trade_log  # noqa: E402

# Strategy note frontmatter id -> (scanner internal STRATEGY_ID, scan fn)
# Paper trading covers A, B, D (C is a confirmed Phase 1A kill -- excluded).
PAPER_STRATEGIES = {
    "STR-A-ma-pullback-fibonacci":     scan_a,
    "STR-B-macd-histogram-divergence": scan_b,
    "STR-D-sr-role-reversal":          scan_d,
}

EXAMPLE_ACCOUNT_SIZE = 100_000  # matches scripts/discord/config.py convention


def _flat_one_pct_stub(signal_dict: dict) -> float:
    """
    TODO(US-067): replace with real per-strategy sizing:
      - Strategy B: Level x Weekly-gate matrix (0.25%-1.0%)
      - Strategy A, D: flat 1% (PS-001) -- these are already correct as-is
    Until US-067 lands, ALL strategies (including B) use flat 1% here.
    """
    return 1.0


def capture(dry_run: bool = False) -> dict:
    summary = {
        "signals_found": 0,
        "opened": 0,
        "skipped_already_open": 0,
        "errors": 0,
        "opened_trades": [],
        "error_details": [],
    }

    print("Loading cached market data...")
    data = load_all()
    if not data:
        summary["note"] = "No cached market data found. Run fetch_data.py first."
        return summary
    print(f"Loaded {len(data)} tickers.")

    for strategy_id, scan_fn in PAPER_STRATEGIES.items():
        print(f"\nScanning {strategy_id}...")
        for ticker, df in data.items():
            try:
                signals = scan_fn(df, ticker)
            except Exception as e:
                summary["errors"] += 1
                summary["error_details"].append(f"{strategy_id}/{ticker} scan error: {e}")
                continue

            if not signals:
                continue

            latest = signals[-1]
            most_recent_bar_date = str(df.index[-1])[:10]
            if str(latest["date"])[:10] != most_recent_bar_date:
                continue  # stale/historical signal, not actionable today

            summary["signals_found"] += 1

            if trade_log.has_open_trade(strategy_id, ticker):
                summary["skipped_already_open"] += 1
                print(f"  SKIP: {strategy_id}/{ticker} already has an open paper trade")
                continue

            entry_date = str(latest["date"])[:10]
            risk_pct = _flat_one_pct_stub(latest)

            entry_price = latest["entry_price"]
            stop_price = latest["stop_price"]
            risk_per_unit = abs(entry_price - stop_price)
            position_size_units = (
                round((EXAMPLE_ACCOUNT_SIZE * risk_pct / 100) / risk_per_unit, 4)
                if risk_per_unit else 0
            )

            trade_dict = {
                "strategy_id": strategy_id,
                "ticker": ticker,
                "asset_class": "stock",
                "data_source": "yfinance",
                "direction": latest["direction"],
                "signal_id": f"{strategy_id}_{ticker}_{entry_date}",
                "entry_date": entry_date,
                "entry_price": entry_price,
                "stop_price": stop_price,
                "target_price": latest["target_price"],
                "position_size_pct": risk_pct,
                "position_size_units": position_size_units,
                "quality_tier": "",  # filled in by alert_publisher's tier logic if available
                "subperiod": latest.get("subperiod", "n/a"),
                "confirmation_level": latest.get("confirmation_level", ""),
                "weekly_gate_scaling": "",  # TODO(US-067)
                "notes": "position_size_pct is a flat-1% stub pending US-067",
            }

            if dry_run:
                summary["opened"] += 1
                summary["opened_trades"].append(trade_dict)
                print(f"  WOULD OPEN: {strategy_id}/{ticker} @ {entry_price} ({entry_date})")
            else:
                try:
                    trade_id = trade_log.open_trade(trade_dict)
                    summary["opened"] += 1
                    trade_dict["trade_id"] = trade_id
                    summary["opened_trades"].append(trade_dict)
                    print(f"  OPENED: {trade_id}")
                except ValueError as e:
                    summary["errors"] += 1
                    summary["error_details"].append(str(e))

    return summary


def main():
    ap = argparse.ArgumentParser(description="HermesForge automatic paper trade signal capture")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be opened without writing to trades.csv")
    args = ap.parse_args()

    summary = capture(dry_run=args.dry_run)

    print(f"\n{'='*60}")
    print(f"SUMMARY: {summary['signals_found']} signals found, "
          f"{summary['opened']} {'would open' if args.dry_run else 'opened'}, "
          f"{summary['skipped_already_open']} skipped (already open), "
          f"{summary['errors']} errors")
    if summary.get("note"):
        print(summary["note"])
    for err in summary.get("error_details", []):
        print(f"  ERROR: {err}")

    print(f"\n--- JSON ---")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
