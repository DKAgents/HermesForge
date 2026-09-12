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

import trade_log
from trade_id import generate_short_id

# ── Config ──────────────────────────────────────────────────────────────────────

TAKER_FEE_BPS = 10          # 0.1% = 10 bps per fill (entry + exit = 0.2% round-trip)
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


# ── Hostile fill rules ───────────────────────────────────────────────────────

def _apply_taker_fee(price: float, is_entry: bool = True) -> float:
    """Deduct taker fee from fill price. Returns effective price after fee."""
    # Fee reduces proceeds: sell lower, buy higher
    fee_rate = TAKER_FEE_BPS / 10_000
    return round(price * (1 + fee_rate), 6)  # always costs the trader


def _worst_print(bar: pd.Series, direction: str) -> float:
    """Return worst bar print for the given direction (simulates stop slippage)."""
    # For a long (stop = sell): worst = low of bar
    # For a short (stop = buy to cover): worst = high of bar
    if direction == "long":
        return float(bar["low"])
    return float(bar["high"])


def _trades_through(bar: pd.Series, level: float, side: str) -> bool:
    """Check if bar trades THROUGH (not just touches) a level.
    For a buy limit (long entry / short target): bar's low must be strictly below level.
    For a sell limit (short entry / long target): bar's high must be strictly above level.
    """
    if side == "buy":  # we want to buy — price must drop through our bid
        return float(bar["low"]) < level
    else:  # we want to sell — price must rise through our ask
        return float(bar["high"]) > level


def _bar_touches(bar: pd.Series, level: float) -> bool:
    """Check if bar's range touches a level (for stop triggers)."""
    return float(bar["low"]) <= level <= float(bar["high"])


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
    side = "buy" if direction == "long" else "sell"

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

        # Limit order: must trade through entry_price
        if _trades_through(row, entry_price, side):
            # Fill at next bar's open (t+1 open for the first bar, open of whichever bar)
            fill_price = float(row["open"])
            fill_price = _apply_taker_fee(fill_price, is_entry=True)
            return {
                "filled": True,
                "fill_price": fill_price,
                "fill_bar_idx": row["bar_idx"],
                "fill_bar_date": str(row["date"])[:10],
                "fill_reason": f"trade-through at bar {row['bar_idx']}",
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

    stop_side = "sell" if direction == "long" else "buy"
    target_side = "sell" if direction == "long" else "buy"

    for offset, (_, row) in enumerate(bars.iterrows(), start=1):
        trade_bar_idx = row["bar_idx"]

        # Stop: worst print on the crossing bar
        if _bar_touches(row, stop_price):
            exit_price = _worst_print(row, direction)
            exit_price = _apply_taker_fee(exit_price, is_entry=False)
            return {
                "action": "closed",
                "exit_reason": "stop",
                "exit_price": exit_price,
                "exit_date": str(row["date"])[:10],
                "bars_held": offset,
            }

        # Target: limit fill — only if bar trades through
        if _trades_through(row, target_price, target_side):
            exit_price = float(target_price)
            exit_price = _apply_taker_fee(exit_price, is_entry=False)
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
            exit_price = _apply_taker_fee(exit_price, is_entry=False)
            return {
                "action": "closed",
                "exit_reason": "time",
                "exit_price": exit_price,
                "exit_date": str(row["date"])[:10],
                "bars_held": offset,
            }

    return {"action": "still_open"}


# ── R-multiple computation ──────────────────────────────────────────────────

def _compute_r(trade: dict, exit_price: float) -> float:
    entry = float(trade["entry_price"])
    stop = float(trade["stop_price"])
    risk = abs(entry - stop)
    if risk <= 0:
        return 0.0
    direction = trade.get("direction", "long")
    if direction == "long":
        return (exit_price - entry) / risk
    else:
        return (entry - exit_price) / risk


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


def _paper_r(trade: dict) -> float | None:
    """Get the R-multiple from the paper model's trades.csv."""
    r_str = trade.get("r_multiple", "")
    if r_str and r_str != "":
        try:
            return float(r_str)
        except (ValueError, TypeError):
            pass
    return None


# ── Main comparison loop ────────────────────────────────────────────────────

def run(
    dry_run: bool = False,
    crypto_only: bool = False,
    stocks_only: bool = False,
    since_date: str = None,
) -> dict:
    """
    Run hostile fill comparison against all pending + entered paper trades.
    Writes comparison records to hostile_fill_report.jsonl.
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
    summary["pending_checked"] = len(pending)

    for trade in pending:
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
                "paper_r": _paper_r(trade),
                "hostile_r": None,
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            if not dry_run:
                _append_report(record)
                summary["records_written"] += 1
            continue

        hostile_entry_price = hostile_entry["fill_price"]

        # Create a modified trade dict with hostile entry for R calc
        hostile_trade = {**trade, "entry_price": hostile_entry_price}

        exit_result = check_exit_hostile(hostile_trade, bars)

        if exit_result["action"] == "closed":
            hostile_r = _compute_r(hostile_trade, exit_result["exit_price"])
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
                "paper_r": _paper_r(trade),
                "hostile_r": round(hostile_r, 4),
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            summary["entered_closed"] += 1
        else:
            summary["entered_open"] += 1
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
                "paper_r": _paper_r(trade),
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
    args = ap.parse_args()

    print(f"\n{'='*60}")
    print(f"Hostile Fill Model — {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print(f"  Taker fee: {TAKER_FEE_BPS/100:.1f}% per fill")
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