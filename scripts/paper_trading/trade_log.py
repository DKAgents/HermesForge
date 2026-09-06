#!/usr/bin/env python3
"""
trade_log.py — HermesForge EPIC-010 (US-065)

Unified paper trade log for stocks and crypto. One CSV schema, one API,
used by every downstream capture/tracking/reporting script so trades are
directly comparable across asset classes and future exchange integrations
(Alpaca, Hyperliquid) write to the same format.

Usage (unit test):
    python3 trade_log.py --test
"""

import sys
import csv
import pathlib
import datetime
from typing import Optional

LOG_PATH = pathlib.Path(__file__).parent / "trades.csv"

FIELDS = [
    "trade_id", "short_id", "strategy_id", "ticker", "asset_class", "data_source",
    "direction", "signal_id", "entry_date", "entry_price", "stop_price", "target_price",
    "position_size_pct", "position_size_units", "quality_tier",
    "entry_status",  # "pending" (waiting for entry fill) or "entered" (filled)
    "status",  # "open" or "closed"
    "exit_date", "exit_price", "exit_reason",
    "r_multiple", "bars_held", "subperiod", "confirmation_level", "weekly_gate_scaling",
    "chart_path", "notes",
    "discord_message_id", "discord_channel_id", "discord_post_url",
]


def _ensure_log():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        with open(LOG_PATH, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()


def make_trade_id(strategy_id: str, ticker: str, entry_date: str) -> str:
    """trade_id = {strategy_id}_{ticker}_{entry_date} — matches US-061 signal_id convention.

    For intraday strategies (STR-Q), entry_date may include a HHMM time suffix
    to disambiguate multiple entries on the same day. For daily strategies,
    entry_date is just YYYY-MM-DD.
    """
    date_part = str(entry_date)[:10]
    return f"{strategy_id}_{ticker}_{date_part}"


def _read_all_rows() -> list[dict]:
    _ensure_log()
    with open(LOG_PATH, newline="") as f:
        return list(csv.DictReader(f))


def _write_all_rows(rows: list[dict]) -> None:
    """Atomic write: temp file → validate → rename.
    
    NEVER truncates the original file before the new write is confirmed.
    Validates row count hasn't dropped by >20% from the existing file.
    On failure: raises ValueError, leaves original file untouched.
    """
    import shutil, os
    
    prev_count = 0
    if LOG_PATH.exists():
        try:
            prev_count = sum(1 for _ in open(LOG_PATH)) - 1  # minus header
        except OSError:
            prev_count = 0
    
    # � Gate 1: refuse to write if row count dropped >20% and >50 rows
    if prev_count > 50 and len(rows) < prev_count * 0.8:
        raise ValueError(
            f"REFUSED: trades.csv would shrink {prev_count}→{len(rows)} rows "
            f"({(1 - len(rows)/prev_count)*100:.0f}% drop). "
            f"Original file preserved. Investigate the caller."
        )
    
    # Gate 2: refuse to write empty rows when file has data
    if prev_count > 10 and len(rows) == 0:
        raise ValueError(
            f"REFUSED: would overwrite {prev_count} rows with empty file. "
            f"Original file preserved."
        )
    
    # Atomic write: temp file → validate → rename
    tmp = LOG_PATH.with_suffix(".tmp")
    try:
        with open(tmp, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
            f.flush()
            os.fsync(f.fileno())   # force to disk
        
        # Verify the temp file is valid
        with open(tmp, newline="") as f:
            verify = list(csv.DictReader(f))
        if len(verify) != len(rows):
            raise ValueError(
                f"Write verification failed: wrote {len(rows)} rows, "
                f"read back {len(verify)} rows. Temp file discarded."
            )
        
        # Atomic replace (rename is atomic on same filesystem)
        shutil.move(str(tmp), str(LOG_PATH))
    except Exception:
        # Clean up temp file on any failure
        tmp.unlink(missing_ok=True)
        raise


def has_open_trade(strategy_id: str, ticker: str) -> bool:
    """Enforces the max-1-open-per-(strategy,ticker) rule."""
    for row in _read_all_rows():
        if row["strategy_id"] == strategy_id and row["ticker"] == ticker and row["status"] == "open":
            return True
    return False


def get_open_trades(strategy_id: Optional[str] = None, ticker: Optional[str] = None) -> list[dict]:
    rows = [r for r in _read_all_rows() if r["status"] == "open"]
    if strategy_id is not None:
        rows = [r for r in rows if r["strategy_id"] == strategy_id]
    if ticker is not None:
        rows = [r for r in rows if r["ticker"] == ticker]
    return rows


def get_pending_trades() -> list[dict]:
    """Trades waiting for entry fill (entry_status == 'pending')."""
    return [r for r in _read_all_rows()
            if r["status"] == "open" and r.get("entry_status", "") == "pending"]


def get_entered_trades() -> list[dict]:
    """Trades that have been entered but not yet closed."""
    return [r for r in _read_all_rows()
            if r["status"] == "open" and r.get("entry_status", "") == "entered"]


def get_trade_by_short_id(short_id: str) -> Optional[dict]:
    """Find a trade by its terse short_id."""
    for row in _read_all_rows():
        if row.get("short_id", "") == short_id:
            return row
    return None


def register_discord_info(trade_id: str, message_id: str, channel_id: str,
                          post_url: str = "") -> None:
    """Update a trade's Discord message info after the setup embed is posted."""
    rows = _read_all_rows()
    for row in rows:
        if row["trade_id"] == trade_id:
            row["discord_message_id"] = message_id
            row["discord_channel_id"] = channel_id
            if post_url:
                row["discord_post_url"] = post_url
            _write_all_rows(rows)
            return
    raise ValueError(f"trade_id not found: {trade_id}")


def update_entry_status(trade_id: str, entry_status: str) -> None:
    """Update a trade's entry_status ('pending' -> 'entered').

    Targets the OPEN row when duplicate trade_ids exist (a strategy may
    re-enter the same ticker+date after a prior close, producing a closed
    row and an open row sharing the same trade_id).
    """
    rows = _read_all_rows()
    target_row = None
    for row in rows:
        if row["trade_id"] == trade_id and row.get("status") == "open":
            target_row = row
            break
    if target_row is None:
        # fall back to any match (legacy behaviour) for safety
        for row in rows:
            if row["trade_id"] == trade_id:
                target_row = row
                break
    if target_row is None:
        raise ValueError(f"trade_id not found: {trade_id}")
    target_row["entry_status"] = entry_status
    _write_all_rows(rows)


def open_trade(trade_dict: dict) -> str:
    """
    Append a new open trade row. trade_dict should contain at least:
    strategy_id, ticker, asset_class, data_source, direction, entry_date,
    entry_price, stop_price, target_price, position_size_pct.
    Optional fields default to empty/None. Returns the generated trade_id.
    """
    _ensure_log()

    required = ["strategy_id", "ticker", "entry_date", "entry_price", "stop_price", "target_price"]
    missing = [f for f in required if f not in trade_dict]
    if missing:
        raise ValueError(f"open_trade missing required fields: {missing}")

    trade_id = make_trade_id(trade_dict["strategy_id"], trade_dict["ticker"], str(trade_dict["entry_date"])[:10])

    if has_open_trade(trade_dict["strategy_id"], trade_dict["ticker"]):
        raise ValueError(
            f"Trade already open for strategy={trade_dict['strategy_id']} ticker={trade_dict['ticker']} "
            f"(max 1 open trade per strategy+ticker pair)"
        )

    row = {field: trade_dict.get(field, "") for field in FIELDS}
    row["trade_id"] = trade_id
    row["status"] = "open"
    row["entry_status"] = trade_dict.get("entry_status", "pending")

    with open(LOG_PATH, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow(row)

    return trade_id


def close_trade(trade_id: str, exit_date: str, exit_price: float, exit_reason: str,
                 bars_held: Optional[int] = None) -> dict:
    """
    Update the trade's row: mark closed, compute r_multiple.
    Returns the updated row dict. Raises if trade_id not found or already closed.
    """
    rows = _read_all_rows()
    target_row = None
    for row in rows:
        if row["trade_id"] == trade_id and row.get("status") == "open":
            target_row = row
            break

    if target_row is None:
        raise ValueError(f"trade_id not found (or already closed): {trade_id}")

    entry_price = float(target_row["entry_price"])
    stop_price = float(target_row["stop_price"])
    direction = target_row["direction"]

    risk = abs(entry_price - stop_price)
    if risk <= 0:
        r_multiple = 0.0
    elif direction == "long":
        r_multiple = (exit_price - entry_price) / risk
    else:  # short
        r_multiple = (entry_price - exit_price) / risk

    target_row["status"] = "closed"
    target_row["exit_date"] = str(exit_date)[:10]
    target_row["exit_price"] = round(exit_price, 4)
    target_row["exit_reason"] = exit_reason
    target_row["r_multiple"] = round(r_multiple, 4)
    if bars_held is not None:
        target_row["bars_held"] = bars_held

    _write_all_rows(rows)
    return target_row


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def _test():
    import tempfile
    global LOG_PATH
    orig_path = LOG_PATH
    LOG_PATH = pathlib.Path(tempfile.mktemp(suffix=".csv"))
    try:
        # --- Long trade: target hit ---
        tid = open_trade({
            "strategy_id": "STR-B-macd-histogram-divergence",
            "ticker": "NVDA",
            "asset_class": "stock",
            "data_source": "yfinance",
            "direction": "long",
            "entry_date": "2026-07-20",
            "entry_price": 100.0,
            "stop_price": 95.0,
            "target_price": 115.0,
            "position_size_pct": 1.0,
        })
        assert tid == "STR-B-macd-histogram-divergence_NVDA_2026-07-20"
        assert has_open_trade("STR-B-macd-histogram-divergence", "NVDA") is True

        # Max-1-open enforcement
        try:
            open_trade({
                "strategy_id": "STR-B-macd-histogram-divergence",
                "ticker": "NVDA",
                "entry_date": "2026-07-21",
                "entry_price": 101.0,
                "stop_price": 96.0,
                "target_price": 116.0,
            })
            assert False, "should have raised on duplicate open trade"
        except ValueError:
            pass

        closed = close_trade(tid, "2026-07-25", 115.0, "target", bars_held=5)
        assert closed["status"] == "closed"
        assert closed["r_multiple"] == 3.0, f"expected R=3.0, got {closed['r_multiple']}"
        assert has_open_trade("STR-B-macd-histogram-divergence", "NVDA") is False

        # --- Short trade: stop hit ---
        tid2 = open_trade({
            "strategy_id": "STR-B-macd-histogram-divergence",
            "ticker": "XOM",
            "asset_class": "stock",
            "data_source": "yfinance",
            "direction": "short",
            "entry_date": "2026-07-20",
            "entry_price": 100.0,
            "stop_price": 105.0,
            "target_price": 85.0,
            "position_size_pct": 0.5,
        })
        closed2 = close_trade(tid2, "2026-07-22", 105.0, "stop", bars_held=2)
        assert closed2["r_multiple"] == -1.0, f"expected R=-1.0, got {closed2['r_multiple']}"

        # --- Double-close should raise ---
        try:
            close_trade(tid2, "2026-07-23", 110.0, "stop")
            assert False, "should have raised on double-close"
        except ValueError:
            pass

        print("✅ All trade_log.py unit tests passed")
    finally:
        LOG_PATH = orig_path


if __name__ == "__main__":
    if "--test" in sys.argv:
        _test()
    else:
        print(__doc__)
