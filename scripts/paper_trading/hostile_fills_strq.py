#!/usr/bin/env python3
"""
hostile_fills_strq.py — Hostile Paper Fill Model for STR-Q-liquidity-sweep (intraday 5m).

Applies hostile fill rules to STR-Q-liquidity-sweep trades using 5m intradday
bars, parallel to the daily hostile_fills.py model.

Rules:
  1. Signal on bar t → fill at t+1 open (or later), only if bar trades THROUGH
     entry price (limit-order semantics).
  2. Taker fee on every fill: 0.1% (10 bps) per side.
  3. Stops fill at worst print on the crossing bar (slippage).
  4. Targets fill only if bar trades through target level (limit).
  5. Time stop at 75 min (15 bars) fills at worst print + taker fee.
  6. Output to hostile_fill_report_strq.jsonl — never touches trades.csv.

Usage:
    python3 hostile_fills_strq.py                    # run full comparison
    python3 hostile_fills_strq.py --dry-run           # show what would be written
    python3 hostile_fills_strq.py --stocks-only
    python3 hostile_fills_strq.py --crypto-only
    python3 hostile_fills_strq.py --force             # clear report and rescore
"""

import sys
import json
import argparse
import pathlib
import datetime
import pandas as pd

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))

import trade_log
from intraday_provider import get_intraday_candles


# ── Config ───────────────────────────────────────────────────────────────────────
TAKER_FEE_BPS = 10           # 0.1% = 10 bps per fill (entry + exit = 0.2% round-trip)
MAX_BARS_HELD = 15           # 75 minutes at 5m resolution
LOOKBACK_BARS = 1000          # ~3.5 days of 5m bars — covers recent STR-Q
STRATEGY_ID = "STR-Q-liquidity-sweep"
REPORT_PATH = pathlib.Path(__file__).parent / "hostile_fill_report_strq.jsonl"


# ── Core helpers ──────────────────────────────────────────────────────────────────
def _apply_taker_fee(price: float, is_entry: bool = True) -> float:
    """Deduct taker fee from fill price. Returns effective price after fee.

    Fee always costs the trader: entry pays slightly more, exit receives slightly less.
    """
    fee_rate = TAKER_FEE_BPS / 10_000
    return round(price * (1 + fee_rate), 6)


def _worst_print(bar: pd.Series, direction: str) -> float:
    """Return worst bar print for the given direction (simulates stop slippage).

    For a long (stop = sell): worst = low of bar.
    For a short (stop = buy to cover): worst = high of bar.
    """
    if direction == "long":
        return float(bar["low"])
    return float(bar["high"])


def _trades_through(bar: pd.Series, level: float, side: str) -> bool:
    """Check if bar trades THROUGH a level (not just touches).

    For a buy limit (long entry / short target): bar's low must be strictly below level.
    For a sell limit (short entry / long target): bar's high must be strictly above level.
    """
    if side == "buy":
        return float(bar["low"]) < level
    else:
        return float(bar["high"]) > level


def _bar_touches(bar: pd.Series, level: float) -> bool:
    """Check if bar's range touches a level (used for stop triggers)."""
    return float(bar["low"]) <= level <= float(bar["high"])


def _compute_r(paper_entry: float, paper_stop: float, direction: str,
               exit_price: float) -> float:
    """Compute R-multiple using paper entry+stop for risk, realized exit for P&L.
    Hostile entry slippage affects P&L direction but risk is fixed by trade setup."""
    risk = abs(paper_entry - paper_stop)
    if risk <= 0:
        return 0.0
    if direction == "long":
        return (exit_price - paper_entry) / risk
    else:
        return (paper_entry - exit_price) / risk


# ── Data loading ───────────────────────────────────────────────────────────────
def _load_bars(ticker: str, asset_class: str) -> pd.DataFrame | None:
    """Load 5m intraday bars for a ticker via intraday_provider.

    The provider returns a DataFame with a 'timestmp' column.
    We rename it to 'date', sort, and add a 'bar_idx' column.

    Returns DataFame with columns: date, open, high, low, close, volume, bar_idx.
    Returns None on failure.
    """
    df = get_intraday_candles(ticker, "5m", asset_class=asset_class, lookback_bars=LOOKBACK_BARS)
    if df is None or df.empty:
        return None

    # intraday_provider returns 'timestamp' column — rename to 'date'
    if "timestamp" in df.columns:
        df = df.rename(columns={"timestamp": "date"})

    # If 'date' is somehow still the index, reset it to a column
    if "date" not in df.columns:
        if df.index.name in ("date", "timestamp", "Datetime"):
            df = df.reset_index()
        # Fallback: try other common column names
        for col in ("timestamp", "Datetime"):
            if col in df.columns:
                df = df.rename(columns={col: "date"})
                break

    if "date" not in df.columns:
        return None

    # Sort by date and assign bar_idx
    df = df.sort_values("date").reset_index(drop=True)
    df["bar_idx"] = range(len(df))
    return df


def _find_signal_bar(bars: pd.DataFrame, entry_date_str: str) -> int | None:
    """Find the bar index whose date matches the trade's entry_date timestmp.

    Maches on the first 16 characters (YYY-MM-DD HH:MM) to align 5m bars
    with the entry signal's timestamp.

    Returns bar_idx (int) or None if no match found.
    """
    entry_ts_prefix = str(entry_date_str)[:16]
    for _, row in bars.iterrows():
        bar_ts_prefix = str(row["date"])[:16]
        if bar_ts_prefix == entry_ts_prefix:
            return int(row["bar_idx"])
    return None


# ── Hostile entry check ───────────────────────────────────────────────────
def check_entry_hostile(trade: dict, bars: pd.DataFrame) -> dict:
    """Check if a trade's entry price has been reached under hostile rules.

    1. Find signal bar matching entry_date timestamp.
    2. Scan bars from signal_bar+1 onward.
    3. First bar that trades through entry_price → fill at that bar's open.
    4. Apply taker fee to fill price.

    Returns: {filled: bool, fill_price: float|None, fill_bar_idx: int|None,
              fill_bar_date: str|None, fill_reason: str}
    """
    entry_price = float(trade["entry_price"])
    direction = trade["direction"]
    side = "buy" if direction == "long" else "sell"

    signal_bar_idx = _find_signal_bar(bars, trade["entry_date"])
    if signal_bar_idx is None:
        # Signal bar not in the cached bar window — can't determine t+1
        return {
            "filled": False,
            "fill_price": None,
            "fill_bar_idx": None,
            "fill_bar_date": None,
            "fill_reason": "signal bar not in cached data (outside 300-bar window)",
        }

    # Scan bars from t+1 onward
    for _, row in bars.iterrows():
        if row["bar_idx"] <= signal_bar_idx:
            continue

        # Limit order: must trade through entry_price
        if _trades_through(row, entry_price, side):
            fill_price = float(row["open"])
            fill_price = _apply_taker_fee(fill_price, is_entry=True)
            return {
                "filled": True,
                "fill_price": fill_price,
                "fill_bar_idx": int(row["bar_idx"]),
                "fill_bar_date": str(row["date"])[:16],
                "fill_reason": f"trade-through at bar {row['bar_idx']}",
            }

    return {
        "filled": False,
        "fill_price": None,
        "fill_bar_idx": None,
        "fill_bar_date": None,
        "fill_reason": "no bar traded through entry level after signal",
    }


# ── Hostile exit check ──────────────────────────────────────────────────
def check_exit_hostile(trade: dict, bars: pd.DataFrame, entry_bar_idx: int) -> dict:
    """Check if an entered trade hits stop/target/time under hostile rules.

    entry_bar_idx: the bar index where the hostile entry was filled.
    Scans bars strictly after entry_bar_idx.

    Rules (checked in order, first hit wins):
      1. Stop: worst print on the crossing bar + taker fee.
      2. Target: limit fill only if bar trades through + taker fee.
      3. Time stop: after MAX_BARS_HELD bars, fill at worst print + taker fee.

    Returns: {action: 'closed'|'still_open', exit_reason, exit_price,
              exit_date, bars_held}
    """
    direction = trade["direction"]
    stop_price = float(trade["stop_price"])
    target_price = float(trade["target_price"])

    stop_side = "sell" if direction == "long" else "buy"
    target_side = "sell" if direction == "long" else "buy"

    for _, row in bars.iterrows():
        if row["bar_idx"] <= entry_bar_idx:
            continue

        bars_held = int(row["bar_idx"]) - entry_bar_idx

        # 1. Stop: worst print on the crossing bar
        if _bar_touches(row, stop_price):
            exit_price = _worst_print(row, direction)
            exit_price = _apply_taker_fee(exit_price, is_entry=False)
            return {
                "action": "closed",
                "exit_reason": "stop",
                "exit_price": exit_price,
                "exit_date": str(row["date"])[:16],
                "bars_held": bars_held,
            }

        # 2. Target: limit fill — only if bar trades through
        if _trades_through(row, target_price, target_side):
            exit_price = float(target_price)
            exit_price = _apply_taker_fee(exit_price, is_entry=False)
            return {
                "action": "closed",
                "exit_reason": "target",
                "exit_price": exit_price,
                "exit_date": str(row["date"])[:16],
                "bars_held": bars_held,
            }

        # 3. Time stop: fill at worst print
        if bars_held >= MAX_BARS_HELD:
            exit_price = _worst_print(row, direction)
            exit_price = _apply_taker_fee(exit_price, is_entry=False)
            return {
                "action": "closed",
                "exit_reason": "time",
                "exit_price": exit_price,
                "exit_date": str(row["date"])[:16],
                "bars_held": bars_held,
            }

    return {"action": "still_open"}


# ── Report writing ───────────────────────────────────────────────────────
def _read_existing_keys() -> set:
    """Read existing trade_id|stage keys from report file for dedup."""
    keys = set()
    if REPORT_PATH.exists():
        try:
            with open(REPORT_PATH) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                        keys.add(f"{r.get('trade_id','')}|{r.get('stage','')}")
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass
    return keys


def _append_report(record: dict, dry_run: bool = False, existing_keys: set = None) -> bool:
    """Append one comparison record to hostile_fill_port_strq.jsonl.

    Deduplicates on (trade_id, stage).
    If dry_run=True, only logs what would be written.
    existing_keys: pre-loaded set of 'trade_id|stage' keys (avoids re-reading file).

    Returns True if the record was written (or would be), False if skipped.
    """
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if existing_keys is None:
        existing_keys = set()
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
                            existing_keys.add(key)
                        except json.JSONDecodeError:
                            pass
            except Exception:
                pass

    key = f"{record.get('trade_id', '')}|{record.get('stage', '')}"
    if key in existing_keys:
        return False

    if dry_run:
        print(f"  [DRY-RUN] Would write: {key}")
        return True

    with open(REPORT_PATH, "a") as f:
        f.write(json.dumps(record, default=str) + "\n")
    return True


def _paper_r(trade: dict) -> float | None:
    """Get the R-multiple from the paper model's trades.csv."""
    r_str = trade.get("r_multiple", "")
    if r_str and r_str != "":
        try:
            return float(r_str)
        except (ValueError, TypeError):
            pass
    return None


# ── Main comparison loop ───────────────────────────────────────────────
def run(dry_run: bool = False, crypto_only: bool = False,
        stocks_only: bool = False, force: bool = False) -> dict:
    """Run hostile fill comparison for all STR-Q-liquidity-sweep trades.

    If force=True, clears the report file before writing (full rescore).
    """
    summary = {
        "total_trades": 0,
        "skipped": 0,
        "open_entry": 0,
        "closed": 0,
        "records_written": 0,
        "errors": 0,
        "error_details": [],
        "paper_r_sum": 0.0,
        "hostile_r_sum": 0.0,
        "paper_wins": 0,
        "hostile_wins": 0,
    }

    # Force: clear existing report
    if force and REPORT_PATH.exists():
        REPORT_PATH.unlink()
        print("  (force: cleared existing report)")

    # Pre-load existing keys for O(1) dedup (avoids re-reading file per record)
    existing_keys = _read_existing_keys() if not force else set()

    # Load all STR-Q trades
    all_rows = trade_log._read_all_rows()
    strq_trades = [r for r in all_rows if r.get("strategy_id") == STRATEGY_ID]

    # ── Pre-load bars per ticker (batch — avoids per-trade fetch) ──
    unique_tickers = set()
    for trade in strq_trades:
        asset_class = trade.get("asset_class", "crypto")
        if crypto_only and asset_class != "crypto":
            continue
        if stocks_only and asset_class != "stock":
            continue
        unique_tickers.add((trade["ticker"], asset_class))

    bars_cache = {}
    for ticker, asset_class in sorted(unique_tickers):
        try:
            bars = _load_bars(ticker, asset_class)
            if bars is not None and not bars.empty:
                bars_cache[(ticker, asset_class)] = bars
        except Exception:
            pass
    print(f"  Pre-loaded bars for {len(bars_cache)}/{len(unique_tickers)} tickers")

    for trade in strq_trades:
        asset_class = trade.get("asset_class", "crypto")
        if crypto_only and asset_class != "crypto":
            continue
        if stocks_only and asset_class != "stock":
            continue

        ticker = trade["ticker"]
        trade_id = trade["trade_id"]
        entry_date = trade.get("entry_date", "")

        summary["total_trades"] += 1

        # ── Load 5m bars (from pre-loaded cache) ──
        bars = bars_cache.get((ticker, asset_class))
        if bars is None:
            summary["errors"] += 1
            summary["error_details"].append(f"{trade_id}: no bar data")
            continue

        # ── Entry check ──
        entry_result = check_entry_hostile(trade, bars)

        if not entry_result["filled"]:
            # Hostile model never entered — skip
            record = {
                "trade_id": trade_id,
                "ticker": ticker,
                "direction": trade["direction"],
                "strategy_id": STRATEGY_ID,
                "stage": "skip",
                "entry_date": entry_date,
                "paper_entry_price": float(trade["entry_price"]),
                "hostile_entry_price": None,
                "hostile_fill_bar": None,
                "hostile_fill_date": None,
                "hostile_fill_reason": entry_result["fill_reason"],
                "paper_r": None,
                "hostile_r": None,
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            if _append_report(record, dry_run=dry_run, existing_keys=existing_keys):
                summary["records_written"] += 1
            summary["skipped"] += 1
            continue

        # ── Entry filled — try exit ──
        hostile_entry_price = entry_result["fill_price"]
        entry_bar_idx = entry_result["fill_bar_idx"]

        # Build a trade dict with hostile entry price for R-computation
        hostile_trade = {**trade, "entry_price": hostile_entry_price}

        paper_closed = trade.get("status", "") == "closed"

        exit_result = check_exit_hostile(hostile_trade, bars, entry_bar_idx)

        if exit_result["action"] == "closed":
            hostile_r = _compute_r(
                paper_entry=float(trade["entry_price"]),
                paper_stop=float(trade["stop_price"]),
                direction=trade["direction"],
                exit_price=exit_result["exit_price"])
            record = {
                "trade_id": trade_id,
                "ticker": ticker,
                "direction": trade["direction"],
                "strategy_id": STRATEGY_ID,
                "stage": "closed",
                "entry_date": entry_date,
                "paper_entry_price": float(trade["entry_price"]),
                "hostile_entry_price": hostile_entry_price,
                "paper_exit_price": float(trade.get("exit_price", 0)) if paper_closed else None,
                "hostile_exit_price": exit_result["exit_price"],
                "paper_exit_reason": trade.get("exit_reason", ""),
                "hostile_exit_reason": exit_result["exit_reason"],
                "hostile_bars_held": exit_result["bars_held"],
                "paper_r": _paper_r(trade),
                "hostile_r": round(hostile_r, 4),
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            summary["closed"] += 1

            # Accumulate aggregate stats
            paper_r = _paper_r(trade)
            if paper_r is not None:
                summary["paper_r_sum"] += paper_r
                if paper_r > 0:
                    summary["paper_wins"] += 1
            if hostile_r is not None:
                summary["hostile_r_sum"] += hostile_r
                if hostile_r > 0:
                    summary["hostile_wins"] += 1

        else:
            # Still open — no exit trigger hit yet
            record = {
                "trade_id": trade_id,
                "ticker": ticker,
                "direction": trade["direction"],
                "strategy_id": STRATEGY_ID,
                "stage": "open_entry",
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
            summary["open_entry"] += 1

        if _append_report(record, dry_run=dry_run, existing_keys=existing_keys):
            summary["records_written"] += 1

    return summary


# ── CLI ──────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description="Hostile Fill Model for STR-Q-liquidity-sweep (intraday 5m)"
    )
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would be written without writing")
    ap.add_argument("--crypto-only", action="store_true",
                    help="Only process crypto trades")
    ap.add_argument("--stocks-only", action="store_true",
                    help="Only process stock trades")
    ap.add_argument("--force", action="store_true",
                    help="Clear report file before run (full rescore, bypass dedup)")
    args = ap.parse_args()

    print(f"\n{'='*60}")
    print(f"STR-Q Hostile Fill Model — {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print(f"  Taker fee: {TAKER_FEE_BPS/100:.1f}% per fill")
    print(f"  Entry rule: t+1 open or later, trade-through required")
    print(f"  Stop rule: worst print on crossing bar")
    print(f"  Target rule: trade-through required (limit)")
    print(f"  Time stop: {MAX_BARS_HELD} bars ({MAX_BARS_HELD * 5} min) at worst print")
    print(f"{'='*60}")

    summary = run(
        dry_run=args.dry_run,
        crypto_only=args.crypto_only,
        stocks_only=args.stocks_only,
        force=args.force,
    )

    n = summary["total_trades"]
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  Total trades:         {n}")
    print(f"  Skip (no fill):       {summary['skipped']}")
    print(f"  Open entry:            {summary['open_entry']}")
    print(f"  Closed (entry+exit):   {summary['closed']}")
    print(f"  Records written:       {summary['records_written']}")
    print(f"  Paper R sum:           {summary['paper_r_sum']:.2f}")
    print(f"  Hostile R sum:         {summary['hostile_r_sum']:.2f}")
    paper_win_rate = (summary["paper_wins"] / n * 100) if n > 0 else 0.0
    hostile_win_rate = (summary["hostile_wins"] / n * 100) if n > 0 else 0.0
    print(f"  Paper win rate:        {paper_win_rate:.1f}%")
    print(f"  Hostile win rate:      {hostile_win_rate:.1f}%")
    print(f"  Errors:                {summary['errors']}")
    for e in summary["error_details"][:10]:
        print(f"    ERROR: {e}")
    if args.dry_run:
        print(f"\n  (dry-run — nothing written to {REPORT_PATH})")
    print()


if __name__ == "__main__":
    main()