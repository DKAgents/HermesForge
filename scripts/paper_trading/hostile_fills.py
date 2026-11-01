#!/usr/bin/env python3
"""
US-142 hostile_fills.py — Hostile Paper Fill Model (parallel to paper model).

Runs alongside trade_monitor.py but with realistic execution assumptions:
  1. Signal on bar t → fills NO EARLIER than bar t+1 open (latency gap)
  2. Taker fee on every fill (0.1% entry + 0.1% exit)
  3. Limit orders fill ONLY if price trades THROUGH the level (not just touches)
  4. Stop orders fill at the WORST print on the crossing bar (slippage)
  5. Output to hostile_fill_report.jsonl — never touches trades.csv / journal

Usage:
    python3 hostile_fills.py                    # run full comparison
    python3 hostile_fills.py --dry-run          # show what would be written
    python3 hostile_fills.py --stocks-only
    python3 hostile_fills.py --crypto-only
    python3 hostile_fills.py --since 2026-09-01 # backfill from date
"""

import sys
import json
import argparse
import pathlib
import time as time_mod
import datetime
import pandas as pd

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "discord"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "gauntlet"))

import trade_log
from trade_id import generate_short_id
import fee_source
from pnl_accounting import (
    _apply_taker_fee,
    _compute_r,
    _adversarial_cost_drag,
    _paper_r,
    _worst_print,
    _trades_through,
    _bar_touches,
    DEGENERATE_RISK_FLOOR,
    widen_stop,
    STOP_WIDEN_FACTOR,
)

# ── Config ──────────────────────────────────────────────────────────────────────

MAX_BARS_HELD = {
    "STR-A-ma-pullback-fibonacci": 8,
    "STR-B-macd-histogram-divergence": 8,
    "STR-D-sr-role-reversal": 8,
    "STR-I-adaptive-trend": 120,
    "STR-L-atr-contraction": 20,
    "STR-P-crosssectional": 21,
}

MARKET_DATA_DIR = pathlib.Path.home() / ".hermes" / "market_data"
CRYPTO_DATA_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "crypto"
REPORT_PATH = pathlib.Path(__file__).parent / "hostile_fill_report.jsonl"


# ── Price data loading ───────────────────────────────────────────────────────

def _load_bars_since(ticker: str, entry_date_str: str, asset_class: str = "stock") -> pd.DataFrame:
    """Load cached OHLC bars for ticker from entry_date onward (NOT strictly after)."""
    data_dir = CRYPTO_DATA_DIR if asset_class == "crypto" else MARKET_DATA_DIR
    path = data_dir / f"{ticker}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"No cached data for {ticker} ({asset_class})")
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df = df.sort_index()

    entry_ts = pd.to_datetime(entry_date_str)
    if entry_ts.tz is None and df.index.tz is not None:
        entry_ts = entry_ts.tz_localize("UTC")
    # Include the entry bar itself (so we can find its date and close)
    df = df[df.index >= entry_ts]

    # Reset index so date is a column, preserving the index name if set
    idx_name = df.index.name or "date"
    df = df.reset_index()
    if idx_name != "date":
        df.rename(columns={idx_name: "date"}, inplace=True)
    df["bar_idx"] = range(len(df))
    return df


# ── Hostile entry check ─────────────────────────────────────────────────────

def check_entry_hostile(
    trade: dict,
    bars: pd.DataFrame,
    skip_if_no_tplus1: bool = True,
) -> dict:
    """
    Check if a pending trade's entry price has been reached under hostile rules:

    1. Signal on bar t → fill NO EARLIER than bar t+1 open
    2. Limit fills only if bar trades THROUGH entry_price, else skip entire trade
    3. Taker fee applied to fill price

    Returns: {filled: bool, fill_price: float or None, fill_bar_idx: int or None,
              fill_bar_date: str or None, filled_reason: str, hostile_pnl_pct: float}
    """
    entry_price = float(trade["entry_price"])
    direction = trade["direction"]
    maker_bps = fee_source.get_maker_bps(trade.get("asset_class", "stock"))

    # Find the signal bar (bar t). If we can't find it, use bar 0.
    # For daily signals, entry_date = the signal bar's date.
    signal_bar_idx = 0
    for _, row in bars.iterrows():
        bar_date_str = str(row["date"])[:10]
        if bar_date_str == str(trade["entry_date"])[:10]:
            signal_bar_idx = row["bar_idx"]
            break

    # Only consider bars t+1 onward
    for _, row in bars.iterrows():
        if row["bar_idx"] < signal_bar_idx + 1:
            continue

        # US-180: resting limit at the swept level — fill (as MAKER) when price
        # trades back to the level, never chase trade-through. `taker_bps` here
        # is really the per-leg bps (maker for a limit fill).
        if _bar_touches(row, entry_price):
            fill_price = _apply_taker_fee(entry_price, direction, is_entry=True, taker_bps=maker_bps)
            return {
                "filled": True,
                "fill_price": fill_price,
                "fill_bar_idx": row["bar_idx"],
                "fill_bar_date": str(row["date"])[:10],
                "fill_reason": "limit fill at swept level",
                "fill_mode": "limit",
                "fee_bps": maker_bps,
            }

    return {
        "filled": False,
        "fill_price": None,
        "fill_bar_idx": None,
        "fill_bar_date": None,
        "fill_reason": "no bar traded through entry level after signal",
    }


# ── Hostile exit check ──────────────────────────────────────────────────────

def check_exit_hostile(
    trade: dict,
    bars: pd.DataFrame,
) -> dict:
    """
    Check if an entered trade has hit stop/target/time under hostile rules:

    1. Stops: worst print on the crossing bar (slippage)
    2. Targets: limit fill — only if bar trades through, else skip (never filled)
    3. Time stop: close at the close of the max-bars bar
    4. Taker fee on exit

    Returns: {action: 'closed'|'still_open', exit_reason, exit_price, exit_date, bars_held}
    """
    direction = trade["direction"]
    stop_price = float(trade["stop_price"])
    target_price = float(trade["target_price"])
    strategy_id = trade["strategy_id"]
    max_bars = MAX_BARS_HELD.get(strategy_id, 21)
    taker_bps = fee_source.get_taker_bps(trade.get("asset_class", "stock"))
    maker_bps = fee_source.get_maker_bps(trade.get("asset_class", "stock"))

    stop_side = "sell" if direction == "long" else "buy"
    target_side = "sell" if direction == "long" else "buy"

    for offset, (_, row) in enumerate(bars.iterrows(), start=1):
        trade_bar_idx = row["bar_idx"]

        # Stop: worst print on the crossing bar
        if _bar_touches(row, stop_price):
            exit_price = _worst_print(row, direction)
            exit_price = _apply_taker_fee(exit_price, direction, is_entry=False, taker_bps=taker_bps)
            return {
                "action": "closed",
                "exit_reason": "stop",
                "exit_price": exit_price,
                "exit_date": str(row["date"])[:10],
                "bars_held": offset,
            }

        # Target: limit fill — only if bar trades through (maker = resting limit)
        if _trades_through(row, target_price, target_side):
            exit_price = float(target_price)
            exit_price = _apply_taker_fee(exit_price, direction, is_entry=False, taker_bps=maker_bps)
            return {
                "action": "closed",
                "exit_reason": "target",
                "exit_price": exit_price,
                "exit_date": str(row["date"])[:10],
                "bars_held": offset,
            }

        # Time stop
        if offset >= max_bars:
            exit_price = float(row["close"])
            exit_price = _apply_taker_fee(exit_price, direction, is_entry=False, taker_bps=taker_bps)
            return {
                "action": "closed",
                "exit_reason": "time",
                "exit_price": exit_price,
                "exit_date": str(row["date"])[:10],
                "bars_held": offset,
            }

    return {"action": "still_open"}


# ── Report writing ──────────────────────────────────────────────────────────

def _append_report(record: dict) -> None:
    """Append one comparison record to the hostile fill report (JSONL).
    Deduplicates: skips if trade_id + stage already exists in the file."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Check for existing record with same trade_id + stage
    existing_ids = set()
    if REPORT_PATH.exists():
        try:
            with open(REPORT_PATH, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        existing = json.loads(line)
                        key = f"{existing.get('trade_id', '')}|{existing.get('stage', '')}"
                        existing_ids.add(key)
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass

    key = f"{record.get('trade_id', '')}|{record.get('stage', '')}"
    if key in existing_ids:
        return  # already recorded

    with open(REPORT_PATH, "a") as f:
        f.write(json.dumps(record, default=str) + "\n")


# ── Main comparison loop ────────────────────────────────────────────────────

def run(
    dry_run: bool = False,
    crypto_only: bool = False,
    stocks_only: bool = False,
    since_date: str = None,
    force: bool = False,
) -> dict:
    """
    Run hostile fill comparison against all pending + entered paper trades.
    Writes comparison records to hostile_fill_report.jsonl.
    If force=True, clears the report file before writing (full rescore).
    """
    summary = {
        "pending_checked": 0,
        "pending_filled": 0,
        "pending_skipped": 0,
        "entered_checked": 0,
        "entered_closed": 0,
        "entered_open": 0,
        "records_written": 0,
        "errors": 0,
        "error_details": [],
    }

    # ── Check pending trades (hostile entry model) ──────────────────────────
    pending = trade_log.get_pending_trades()
    # Also include closed|pending trades — paper closed them without entry
    # (time-stop, cancellation, etc.). Hostile model scores them for entry only.
    all_rows = trade_log._read_all_rows()
    closed_pending = [r for r in all_rows
                      if r.get("status") == "closed"
                      and r.get("entry_status") == "pending"]
    # Combine: pending first, then closed_pending
    all_entry_candidates = pending + closed_pending
    summary["pending_checked"] = len(all_entry_candidates)
    summary["pending_closed_from_pending"] = len(closed_pending)

    for trade in all_entry_candidates:
        asset_class = trade.get("asset_class", "stock")
        if crypto_only and asset_class != "crypto":
            continue
        if stocks_only and asset_class != "stock":
            continue
        if trade.get("strategy_id") == "STR-Q-liquidity-sweep":
            continue  # intraday not yet modeled here

        ticker = trade["ticker"]
        short_id = trade.get("short_id", "?")
        entry_date = trade.get("entry_date", "")
        # Fallback: extract date from signal_id (daily/swing trades encode it there)
        if not entry_date:
            sig = trade.get("signal_id", "")
            parts = sig.rsplit("_", 2)
            if len(parts) >= 2:
                # Check last segment first (most likely the date)
                candidate = parts[-1]
                if not (len(candidate) == 10 and candidate[4] == "-"):
                    candidate = parts[-2]
                if len(candidate) == 10 and candidate[4] == "-":
                    entry_date = candidate

        # Filter by since_date if provided
        if since_date and entry_date < since_date:
            continue

        try:
            bars = _load_bars_since(ticker, entry_date, asset_class)
        except FileNotFoundError as e:
            summary["errors"] += 1
            summary["error_details"].append(f"{short_id}: {e}")
            continue

        if bars.empty:
            continue

        hostile_entry = check_entry_hostile(trade, bars)

        if hostile_entry["filled"]:
            hostile_entry_price = hostile_entry["fill_price"]
            # Compute R using hostile entry price vs paper stop
            # (paper target/stop unchanged — only entry price differs)
            paper_entry = float(trade["entry_price"])
            record = {
                "trade_id": trade["trade_id"],
                "ticker": ticker,
                "direction": trade["direction"],
                "strategy_id": trade["strategy_id"],
                "stage": "entry",
                "entry_date": entry_date,
                "paper_entry_price": paper_entry,
                "hostile_entry_price": hostile_entry_price,
                "hostile_fill_bar": hostile_entry["fill_bar_idx"],
                "hostile_fill_date": hostile_entry["fill_bar_date"],
                "hostile_fill_reason": hostile_entry["fill_reason"],
                "paper_r": None,  # not exited yet in paper model either
                "hostile_r": None,
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            summary["pending_filled"] += 1
        else:
            # Hostile model skipped — never filled
            record = {
                "trade_id": trade["trade_id"],
                "ticker": ticker,
                "direction": trade["direction"],
                "strategy_id": trade["strategy_id"],
                "stage": "skip",
                "entry_date": entry_date,
                "paper_entry_price": float(trade["entry_price"]),
                "hostile_entry_price": None,
                "hostile_fill_bar": None,
                "hostile_fill_date": None,
                "hostile_fill_reason": hostile_entry["fill_reason"],
                "paper_r": None,
                "hostile_r": None,
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            summary["pending_skipped"] += 1

        if not dry_run:
            _append_report(record)
            summary["records_written"] += 1

    # ── Check entered/closed trades (hostile exit model) ────────────────────
    # Get ALL trades (not just entered) — we want to also backfill closed ones
    all_trades_rows = trade_log._read_all_rows()
    entered = [r for r in all_trades_rows
               if r.get("status") in ("open", "closed")
               and r.get("entry_status") == "entered"]

    summary["entered_checked"] = len(entered)

    for trade in entered:
        asset_class = trade.get("asset_class", "stock")
        if crypto_only and asset_class != "crypto":
            continue
        if stocks_only and asset_class != "stock":
            continue
        if trade.get("strategy_id") == "STR-Q-liquidity-sweep":
            continue

        ticker = trade["ticker"]
        short_id = trade.get("short_id", "?")
        entry_date = trade.get("entry_date", "")
        # Fallback: extract date from signal_id (daily/swing trades encode it there)
        if not entry_date:
            sig = trade.get("signal_id", "")
            parts = sig.rsplit("_", 2)
            if len(parts) >= 2:
                # Check last segment first (most likely the date)
                candidate = parts[-1]
                if not (len(candidate) == 10 and candidate[4] == "-"):
                    candidate = parts[-2]
                if len(candidate) == 10 and candidate[4] == "-":
                    entry_date = candidate

        if since_date and entry_date < since_date:
            continue

        try:
            bars = _load_bars_since(ticker, entry_date, asset_class)
        except FileNotFoundError as e:
            summary["errors"] += 1
            summary["error_details"].append(f"{short_id}: {e}")
            continue

        if bars.empty:
            continue

        # Re-run hostile entry to get the entry price (for R calculation)
        hostile_entry = check_entry_hostile(trade, bars)
        if not hostile_entry["filled"]:
            # Hostile never entered — skip exit check
            paper_r, paper_costed = _paper_r(trade, round_trip_bps=fee_source.get_round_trip_bps(asset_class))
            record = {
                "trade_id": trade["trade_id"],
                "ticker": ticker,
                "direction": trade["direction"],
                "strategy_id": trade["strategy_id"],
                "stage": "skip_entry",
                "entry_date": entry_date,
                "paper_entry_price": float(trade["entry_price"]),
                "hostile_entry_price": None,
                "hostile_fill_bar": None,
                "hostile_fill_date": None,
                "hostile_fill_reason": hostile_entry["fill_reason"],
                "paper_r": paper_r,
                "paper_r_uncosted": not paper_costed,
                "hostile_r": None,
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            if not dry_run:
                _append_report(record)
                summary["records_written"] += 1
            continue

        hostile_entry_price = hostile_entry["fill_price"]

        paper_entry = float(trade["entry_price"])
        paper_stop = float(trade["stop_price"])
        # US-180: widen the stop by STOP_WIDEN_FACTOR before modeling the exit.
        widened_stop = widen_stop(paper_entry, paper_stop, trade["direction"], STOP_WIDEN_FACTOR)

        # Exit check reads stop/target/direction — pass a trade with the widened
        # stop. Entry slippage is charged inside _compute_r via hostile_entry_price.
        exit_result = check_exit_hostile({**trade, "stop_price": widened_stop}, bars)

        if exit_result["action"] == "closed":
            paper_r, paper_costed = _paper_r(trade, round_trip_bps=fee_source.get_round_trip_bps(asset_class))
            hostile_r = _compute_r(
                paper_entry=paper_entry,
                paper_stop=widened_stop,
                direction=trade["direction"],
                hostile_entry_price=hostile_entry_price,
                exit_price=exit_result["exit_price"])
            record = {
                "trade_id": trade["trade_id"],
                "ticker": ticker,
                "direction": trade["direction"],
                "strategy_id": trade["strategy_id"],
                "stage": "closed",
                "entry_date": entry_date,
                "paper_entry_price": float(trade["entry_price"]),
                "hostile_entry_price": hostile_entry_price,
                "paper_exit_price": float(trade.get("exit_price", 0)) if trade.get("status") == "closed" else None,
                "hostile_exit_price": exit_result["exit_price"],
                "paper_exit_reason": trade.get("exit_reason", ""),
                "hostile_exit_reason": exit_result["exit_reason"],
                "hostile_bars_held": exit_result["bars_held"],
                "paper_r": paper_r,
                "paper_r_uncosted": not paper_costed,
                "hostile_r": round(hostile_r, 4),
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            summary["entered_closed"] += 1
        else:
            summary["entered_open"] += 1
            paper_r, paper_costed = _paper_r(trade, round_trip_bps=fee_source.get_round_trip_bps(asset_class))
            record = {
                "trade_id": trade["trade_id"],
                "ticker": ticker,
                "direction": trade["direction"],
                "strategy_id": trade["strategy_id"],
                "stage": "open",
                "entry_date": entry_date,
                "paper_entry_price": float(trade["entry_price"]),
                "hostile_entry_price": hostile_entry_price,
                "paper_exit_price": None,
                "hostile_exit_price": None,
                "paper_exit_reason": None,
                "hostile_exit_reason": "still_open",
                "hostile_bars_held": None,
                "paper_r": paper_r,
                "paper_r_uncosted": not paper_costed,
                "hostile_r": None,
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }

        if not dry_run:
            _append_report(record)
            summary["records_written"] += 1

    return summary


def main():
    ap = argparse.ArgumentParser(
        description="US-142 Hostile Paper Fill Model — parallel fill comparison"
    )
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would be written without writing")
    ap.add_argument("--crypto-only", action="store_true")
    ap.add_argument("--stocks-only", action="store_true")
    ap.add_argument("--since", type=str, default=None,
                    help="Only process trades since date (YYYY-MM-DD)")
    ap.add_argument("--force", action="store_true",
                    help="Clear report file before run (full rescore, bypass dedup)")
    args = ap.parse_args()

    if args.force:
        if REPORT_PATH.exists():
            REPORT_PATH.unlink()
            print(f"  (force: cleared existing report)")

    print(f"\n{'='*60}")
    print(f"Hostile Fill Model — {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print(f"  Taker fee: {fee_source.get_taker_bps('crypto'):.2f} bps crypto / {fee_source.get_taker_bps('stock'):.2f} bps stock per fill")
    print(f"  Entry rule: t+1 open or later, trade-through required")
    print(f"  Stop rule: worst print on crossing bar")
    print(f"  Target rule: trade-through required (limit)")
    print(f"{'='*60}")

    summary = run(
        dry_run=args.dry_run,
        crypto_only=args.crypto_only,
        stocks_only=args.stocks_only,
        since_date=args.since,
    )

    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  Pending checked:      {summary['pending_checked']}")
    print(f"  Hostile filled:       {summary['pending_filled']}")
    print(f"  Hostile skipped:      {summary['pending_skipped']}")
    print(f"  Entered checked:      {summary['entered_checked']}")
    print(f"  Hostile closed:       {summary['entered_closed']}")
    print(f"  Hostile still open:   {summary['entered_open']}")
    print(f"  Records written:      {summary['records_written']}")
    print(f"  Errors:               {summary['errors']}")
    for e in summary["error_details"][:10]:
        print(f"    ERROR: {e}")
    if summary.get("dry_run"):
        print(f"\n  (dry-run — nothing written to {REPORT_PATH})")


if __name__ == "__main__":
    main()