#!/usr/bin/env python3
"""
near_miss_tracker.py — Track near-miss signals and filter out played-out trades.

Keeps a JSON log of recently posted near-miss signals (ticker, direction, stop,
entry, date). On each scan, checks if any previously posted near-miss has had
its stop hit since the signal date. If so, that ticker is excluded from new
near-miss results — the trade already played out, no point showing it again.

State file: ~/.hermes/market_data/near_miss_state.json
"""

import json
import pathlib
import pandas as pd
from datetime import datetime, timedelta

STATE_FILE = pathlib.Path.home() / ".hermes" / "market_data" / "near_miss_state.json"
STALE_DAYS = 30  # Remove entries older than this (they've had time to play out)


def _load_state() -> dict:
    """Load the near-miss state file. Returns empty dict if not found."""
    if not STATE_FILE.exists():
        return {"signals": []}
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"signals": []}


def _save_state(state: dict):
    """Save the near-miss state file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def record_near_miss(ticker: str, direction: str, entry_price: float,
                     stop_price: float, signal_date: str, strategy_id: str):
    """Record a newly posted near-miss signal."""
    state = _load_state()
    state["signals"].append({
        "ticker": ticker,
        "direction": direction,
        "entry_price": entry_price,
        "stop_price": stop_price,
        "signal_date": signal_date,
        "strategy_id": strategy_id,
        "recorded_at": datetime.now().isoformat(),
        "status": "active",  # active → stopped_out → expired
    })
    _save_state(state)


def _check_stopped_out(signal: dict, data_cache_dir: pathlib.Path,
                       asset_class: str) -> bool:
    """
    Check if a previously posted near-miss has been stopped out.
    Returns True if the stop has been hit since the signal date.
    """
    ticker = signal["ticker"]
    stop_price = signal["stop_price"]
    signal_date_str = signal["signal_date"]
    direction = signal.get("direction", "long")

    # Find the parquet file
    if asset_class == "crypto":
        parquet_path = data_cache_dir / "crypto" / f"{ticker}.parquet"
    else:
        parquet_path = data_cache_dir / f"{ticker}.parquet"

    if not parquet_path.exists():
        return False

    try:
        df = pd.read_parquet(parquet_path)
        # Get bars after the signal date
        signal_date = pd.Timestamp(signal_date_str)
        future_bars = df[df.index > signal_date]
        if future_bars.empty:
            return False

        if direction == "long":
            # Stop is below entry — check if any low went below stop
            if (future_bars["low"] <= stop_price).any():
                return True
        else:
            # Short: stop is above entry — check if any high went above stop
            if (future_bars["high"] >= stop_price).any():
                return True
    except Exception:
        return False

    return False


def get_excluded_tickers(data_cache_dir: pathlib.Path) -> set[str]:
    """
    Get the set of tickers that should be excluded from near-miss results
    because a previously posted near-miss has already stopped out.

    Also cleans up stale entries (older than STALE_DAYS).
    """
    state = _load_state()
    excluded = set()
    now = datetime.now()
    cutoff = now - timedelta(days=STALE_DAYS)

    active_signals = []
    for sig in state.get("signals", []):
        recorded_at = sig.get("recorded_at", "")
        try:
            recorded_dt = datetime.fromisoformat(recorded_at)
        except (ValueError, TypeError):
            recorded_dt = cutoff

        # Remove stale entries
        if recorded_dt < cutoff:
            continue

        # Check if stopped out
        if sig.get("status") == "active":
            asset_class = "crypto" if sig["ticker"] in _get_crypto_tickers() else "stock"
            if _check_stopped_out(sig, data_cache_dir, asset_class):
                sig["status"] = "stopped_out"

        if sig.get("status") == "stopped_out":
            excluded.add(sig["ticker"])

        # Keep ALL non-stale signals (active + stopped_out) in state
        # Stopped-out signals persist until they expire by age, so the ticker
        # stays excluded until a fresh signal fires after the stale window
        active_signals.append(sig)

    # Save cleaned state
    state["signals"] = active_signals
    _save_state(state)

    return excluded


def _get_crypto_tickers() -> set[str]:
    """Get the set of known crypto tickers."""
    try:
        import sys
        sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "paper_trading"))
        from fetch_crypto_data import CRYPTO_UNIVERSE
        return set(CRYPTO_UNIVERSE)
    except Exception:
        return set()


def filter_near_misses(results: list[dict], data_cache_dir: pathlib.Path) -> list[dict]:
    """
    Filter near-miss results to remove tickers that have already stopped out
    from a previously posted near-miss signal.

    Also records new near-miss signals for future filtering.
    """
    excluded = get_excluded_tickers(data_cache_dir)

    filtered = []
    for r in results:
        if r["ticker"] in excluded:
            # This ticker had a near-miss that already stopped out — skip it
            continue
        filtered.append(r)

    # Record the new near-misses we're about to show
    for r in filtered:
        record_near_miss(
            ticker=r["ticker"],
            direction=r.get("direction", "long"),
            entry_price=r["entry_price"],
            stop_price=r["stop_price"],
            signal_date=r["date"],
            strategy_id=r["strategy_id"],
        )

    return filtered
