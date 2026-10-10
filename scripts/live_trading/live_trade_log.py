#!/usr/bin/env python3
"""
live_trade_log.py — Separate journal for live trades.

NEVER writes to the paper trades.csv. Live trades live in their own CSV
so paper performance stats remain unpolluted.

Schema mirrors trades.csv but with live-specific fields:
  trade_id, strategy_id, ticker, direction, entry_date, entry_price,
  stop_price, target_price, size_usd, position_size_units, status,
  exit_date, exit_price, exit_reason, pnl_usd, r_multiple, notes
"""

from __future__ import annotations

import csv
import os
import fcntl
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

LOG_PATH = Path(os.environ.get(
    "LIVE_TRADE_LOG",
    str(Path("/root/HermesForge/scripts/live_trading/trades_live.csv"))
))

FIELD_NAMES = [
    "trade_id", "strategy_id", "ticker", "direction",
    "entry_date", "entry_price", "stop_price", "target_price",
    "size_usd", "position_size_units", "status",
    "exit_date", "exit_price", "exit_reason",
    "pnl_usd", "r_multiple", "notes",
]


def _ensure_log():
    """Create log file with headers if it doesn't exist."""
    if not LOG_PATH.exists():
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELD_NAMES)
            writer.writeheader()


def _read_all_rows() -> list[dict]:
    _ensure_log()
    with open(LOG_PATH, newline="") as f:
        return list(csv.DictReader(f))


def _write_all_rows(rows: list[dict]):
    """Atomic write: temp file → validate → rename."""
    tmp = LOG_PATH.with_suffix(".csv.tmp")
    with open(tmp, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELD_NAMES)
        writer.writeheader()
        for row in rows:
            filtered = {k: row.get(k, "") for k in FIELD_NAMES}
            writer.writerow(filtered)
    # Atomic rename (same filesystem)
    os.replace(tmp, LOG_PATH)


def open_trade(trade_dict: dict) -> str:
    """
    Record a new live trade. Returns trade_id.
    """
    _ensure_log()

    trade_id = trade_dict.get("trade_id", "")
    if not trade_id:
        raise ValueError("trade_id is required")

    rows = _read_all_rows()

    # Check for duplicates
    for row in rows:
        if row.get("trade_id") == trade_id and row.get("status") == "open":
            raise ValueError(f"Trade already open: {trade_id}")

    entry_date = trade_dict.get("entry_date", datetime.now(timezone.utc).isoformat())

    rows.append({
        "trade_id": trade_id,
        "strategy_id": trade_dict.get("strategy_id", ""),
        "ticker": trade_dict.get("ticker", ""),
        "direction": trade_dict.get("direction", "long"),
        "entry_date": entry_date,
        "entry_price": trade_dict.get("entry_price", ""),
        "stop_price": trade_dict.get("stop_price", ""),
        "target_price": trade_dict.get("target_price", ""),
        "size_usd": trade_dict.get("size_usd", ""),
        "position_size_units": trade_dict.get("position_size_units", ""),
        "status": "open",
        "exit_date": "",
        "exit_price": "",
        "exit_reason": "",
        "pnl_usd": "",
        "r_multiple": "",
        "notes": trade_dict.get("notes", ""),
    })

    _write_all_rows(rows)
    return trade_id


def close_trade(trade_id: str, exit_price: float, exit_reason: str,
                pnl_usd: float = 0.0) -> dict:
    """
    Close an open live trade.
    """
    rows = _read_all_rows()
    target_row = None
    for row in rows:
        if row["trade_id"] == trade_id and row["status"] == "open":
            target_row = row
            break

    if target_row is None:
        raise ValueError(f"Live trade not found or already closed: {trade_id}")

    entry_price = float(target_row["entry_price"])
    stop_price = float(target_row["stop_price"])
    direction = target_row["direction"]

    risk = abs(entry_price - stop_price)
    if risk <= 0:
        r_multiple = 0.0
    elif direction == "long":
        r_multiple = (exit_price - entry_price) / risk
    else:
        r_multiple = (entry_price - exit_price) / risk

    exit_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    target_row["status"] = "closed"
    target_row["exit_date"] = exit_date
    target_row["exit_price"] = str(round(exit_price, 4))
    target_row["exit_reason"] = exit_reason
    target_row["pnl_usd"] = str(round(pnl_usd, 2))
    target_row["r_multiple"] = str(round(r_multiple, 4))

    _write_all_rows(rows)
    return target_row


def get_open_trades() -> list[dict]:
    """Get all currently open live trades."""
    _ensure_log()
    return [r for r in _read_all_rows() if r["status"] == "open"]


def get_closed_trades(n: int = 100) -> list[dict]:
    """Get the most recent N closed trades."""
    _ensure_log()
    closed = [r for r in _read_all_rows() if r["status"] == "closed"]
    return closed[-n:]


def get_total_live_pnl() -> float:
    """Get total realized P&L from closed live trades."""
    _ensure_log()
    total = 0.0
    for r in _read_all_rows():
        if r["status"] == "closed":
            try:
                total += float(r.get("pnl_usd", 0) or 0)
            except (ValueError, TypeError):
                pass
    return total


# ── Convenience ────────────────────────────────────────────────────────
def live_summary() -> dict:
    """Quick summary of live trading activity."""
    _ensure_log()
    rows = _read_all_rows()
    open_trades = [r for r in rows if r["status"] == "open"]
    closed = [r for r in rows if r["status"] == "closed"]

    total_pnl = 0.0
    wins = 0
    losses = 0
    for r in closed:
        try:
            pnl = float(r.get("pnl_usd", 0) or 0)
            total_pnl += pnl
            if pnl > 0:
                wins += 1
            elif pnl < 0:
                losses += 1
        except (ValueError, TypeError):
            pass

    total_exposure = sum(
        float(t.get("size_usd", 0) or 0) for t in open_trades
    )

    return {
        "open_positions": len(open_trades),
        "total_exposure_usd": round(total_exposure, 2),
        "closed_trades": len(closed),
        "total_pnl_usd": round(total_pnl, 2),
        "win_rate": round(wins / max(wins + losses, 1), 2),
        "wins": wins,
        "losses": losses,
    }


# ── Test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Live Trade Log ===\n")
    s = live_summary()
    for k, v in s.items():
        print(f"  {k}: {v}")