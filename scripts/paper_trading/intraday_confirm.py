#!/usr/bin/env python3
"""
intraday_confirm.py — HermesForge Intraday Confirmation Layer (Phase 1: Crypto)

After a daily-bar crypto signal fires, fetches the next 1h candles from
Hyperliquid's free public API and checks if the signal survives the first
4 hours. Only confirmed signals pass through to publishing.

Confirmation criteria (all must pass):
  1. PRICE HOLD: no 1h bar's low (long) / high (short) touches the stop
  2. MOMENTUM: at least 2 of 4 hourly bars close in the signal direction
  3. VOLUME: at least 1 bar has volume > 20-bar average hourly volume

If any criterion fails, the signal is rejected with a documented reason.

Hyperliquid API: same candleSnapshot endpoint as fetch_crypto_data.py,
just with interval="1h" instead of "1d". No auth, no cost, full history.

Usage:
    from intraday_confirm import confirm_signal, confirm_signals

    # Confirm a single signal
    result = confirm_signal(signal_dict)
    if result["confirmed"]:
        publish_signal(signal_dict)
    else:
        log_rejection(signal_dict, result["reason"])

    # Confirm a batch (returns confirmed + rejected lists)
    confirmed, rejected = confirm_signals(signal_list)
"""

import datetime
import requests
import pandas as pd
import numpy as np
from typing import Optional

HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"

# How many hourly bars to check after the daily signal
CONFIRMATION_HOURS = 4

# Minimum bars that must close in signal direction
MIN_DIRECTIONAL_BARS = 2

# How many bars of 1h volume to average for the volume check
VOLUME_LOOKBACK = 20


def fetch_hourly_candles(symbol: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    """Fetch 1h candles from Hyperliquid for a symbol between timestamps."""
    resp = requests.post(
        HYPERLIQUID_INFO_URL,
        json={
            "type": "candleSnapshot",
            "req": {
                "coin": symbol,
                "interval": "1h",
                "startTime": start_ms,
                "endTime": end_ms,
            },
        },
        timeout=30,
    )
    resp.raise_for_status()
    candles = resp.json()
    if not candles:
        return pd.DataFrame()

    rows = []
    for c in candles:
        rows.append(
            {
                "date": pd.to_datetime(c["t"], unit="ms"),
                "open": float(c["o"]),
                "high": float(c["h"]),
                "low": float(c["l"]),
                "close": float(c["c"]),
                "volume": float(c["v"]),
            }
        )

    df = pd.DataFrame(rows).set_index("date").sort_index()
    return df


def confirm_signal(signal: dict, verbose: bool = False) -> dict:
    """
    Check if a daily crypto signal survives intraday confirmation.

    Args:
        signal: dict with keys:
            - ticker: Hyperliquid symbol (e.g. "BTC", "ETH")
            - direction: "long" or "short"
            - entry_price: float
            - stop_price: float
            - date: signal date (str or Timestamp, the daily bar date)
        verbose: print debug info

    Returns:
        {
            "confirmed": bool,
            "reason": str,           # "confirmed" or rejection reason
            "bars_checked": int,     # how many 1h bars were checked
            "hourly_data": DataFrame,  # the 1h bars used
            "details": dict,        # per-criterion breakdown
        }
    """
    ticker = signal.get("ticker", "")
    direction = signal.get("direction", "long")
    entry_price = float(signal.get("entry_price", 0))
    stop_price = float(signal.get("stop_price", 0))
    signal_date = signal.get("date", "")

    if not ticker or not entry_price or not stop_price:
        return {
            "confirmed": False,
            "reason": "Missing required signal fields (ticker, entry_price, stop_price)",
            "bars_checked": 0,
            "hourly_data": pd.DataFrame(),
            "details": {},
        }

    # Parse signal date and compute the confirmation window
    # Daily bar date = the day the signal fired. Confirmation = next day's first N hours.
    if isinstance(signal_date, str):
        signal_date = pd.Timestamp(signal_date).tz_localize(None) if pd.Timestamp(signal_date).tz else pd.Timestamp(signal_date)
    elif isinstance(signal_date, pd.Timestamp):
        signal_date = signal_date.tz_localize(None) if signal_date.tz else signal_date

    # Start of the next day (UTC)
    next_day_start = signal_date.normalize() + pd.Timedelta(days=1)
    # End = next_day_start + CONFIRMATION_HOURS hours + some buffer for volume lookback
    fetch_start_ms = int(next_day_start.timestamp() * 1000) - (VOLUME_LOOKBACK * 3600 * 1000)
    fetch_end_ms = int((next_day_start + pd.Timedelta(hours=CONFIRMATION_HOURS + 2)).timestamp() * 1000)

    if verbose:
        print(f"  Confirming {ticker} {direction} signal from {signal_date.date()}")
        print(f"  Fetching 1h bars from {next_day_start} to {next_day_start + pd.Timedelta(hours=CONFIRMATION_HOURS)}")

    # Fetch hourly candles
    try:
        hourly = fetch_hourly_candles(ticker, fetch_start_ms, fetch_end_ms)
    except Exception as e:
        return {
            "confirmed": False,
            "reason": f"Failed to fetch 1h data: {e}",
            "bars_checked": 0,
            "hourly_data": pd.DataFrame(),
            "details": {},
        }

    if hourly.empty or len(hourly) < CONFIRMATION_HOURS:
        return {
            "confirmed": False,
            "reason": f"Insufficient 1h data ({len(hourly)} bars, need {CONFIRMATION_HOURS})",
            "bars_checked": len(hourly) if not hourly.empty else 0,
            "hourly_data": hourly,
            "details": {},
        }

    # Extract the confirmation window (first CONFIRMATION_HOURS bars of the next day)
    confirm_bars = hourly[hourly.index >= next_day_start].head(CONFIRMATION_HOURS)

    if len(confirm_bars) < CONFIRMATION_HOURS:
        return {
            "confirmed": False,
            "reason": f"Only {len(confirm_bars)} bars in confirmation window (need {CONFIRMATION_HOURS})",
            "bars_checked": len(confirm_bars),
            "hourly_data": hourly,
            "details": {},
        }

    details = {}

    # ── Criterion 1: PRICE HOLD ─────────────────────────────────────────────
    # No bar's low (long) / high (short) should touch the stop
    if direction == "long":
        worst_bar = confirm_bars["low"].min()
        price_holds = worst_bar > stop_price
        details["price_hold"] = {
            "passed": price_holds,
            "worst_low": worst_bar,
            "stop_price": stop_price,
        }
        if not price_holds:
            return {
                "confirmed": False,
                "reason": f"Stop hit intraday: low {worst_bar:.4f} <= stop {stop_price:.4f}",
                "bars_checked": CONFIRMATION_HOURS,
                "hourly_data": hourly,
                "details": details,
            }
    else:  # short
        worst_bar = confirm_bars["high"].max()
        price_holds = worst_bar < stop_price
        details["price_hold"] = {
            "passed": price_holds,
            "worst_high": worst_bar,
            "stop_price": stop_price,
        }
        if not price_holds:
            return {
                "confirmed": False,
                "reason": f"Stop hit intraday: high {worst_bar:.4f} >= stop {stop_price:.4f}",
                "bars_checked": CONFIRMATION_HOURS,
                "hourly_data": hourly,
                "details": details,
            }

    # ── Criterion 2: MOMENTUM ───────────────────────────────────────────────
    # At least MIN_DIRECTIONAL_BARS of CONFIRMATION_HOURS bars must close in direction
    if direction == "long":
        directional_bars = (confirm_bars["close"] > confirm_bars["open"]).sum()
    else:
        directional_bars = (confirm_bars["close"] < confirm_bars["open"]).sum()

    momentum_passes = directional_bars >= MIN_DIRECTIONAL_BARS
    details["momentum"] = {
        "passed": momentum_passes,
        "directional_bars": int(directional_bars),
        "required": MIN_DIRECTIONAL_BARS,
        "total_bars": CONFIRMATION_HOURS,
    }

    if not momentum_passes:
        return {
            "confirmed": False,
            "reason": f"Momentum insufficient: only {directional_bars}/{CONFIRMATION_HOURS} bars in direction",
            "bars_checked": CONFIRMATION_HOURS,
            "hourly_data": hourly,
            "details": details,
        }

    # ── Criterion 3: VOLUME CONFIRMATION ───────────────────────────────────
    # At least 1 bar in the confirmation window must have volume > 20-bar average
    # Use the pre-window bars as the volume baseline
    pre_window = hourly[hourly.index < next_day_start].tail(VOLUME_LOOKBACK)

    if len(pre_window) >= 5:  # need at least 5 bars for a meaningful average
        avg_volume = pre_window["volume"].mean()
        max_confirm_volume = confirm_bars["volume"].max()
        volume_passes = max_confirm_volume > avg_volume
        details["volume"] = {
            "passed": volume_passes,
            "max_confirm_volume": float(max_confirm_volume),
            "avg_baseline_volume": float(avg_volume),
            "baseline_bars": len(pre_window),
        }
    else:
        # Not enough pre-window data — skip volume check (don't fail on this)
        volume_passes = True
        details["volume"] = {
            "passed": True,
            "note": f"Skipped (only {len(pre_window)} pre-window bars for baseline)",
        }

    if not volume_passes:
        return {
            "confirmed": False,
            "reason": f"Volume insufficient: max {max_confirm_volume:.0f} <= avg {avg_volume:.0f}",
            "bars_checked": CONFIRMATION_HOURS,
            "hourly_data": hourly,
            "details": details,
        }

    # ── All criteria passed ─────────────────────────────────────────────────
    if verbose:
        print(f"  ✅ CONFIRMED: all 3 criteria passed")

    return {
        "confirmed": True,
        "reason": "confirmed",
        "bars_checked": CONFIRMATION_HOURS,
        "hourly_data": hourly,
        "details": details,
    }


def confirm_signals(signals: list, verbose: bool = False) -> tuple:
    """
    Confirm a batch of signals. Returns (confirmed_list, rejected_list).

    Each confirmed signal gets an added "confirmation" key with details.
    Each rejected signal gets an added "rejection" key with the reason.
    """
    confirmed = []
    rejected = []

    for sig in signals:
        result = confirm_signal(sig, verbose=verbose)

        if result["confirmed"]:
            sig["confirmation"] = {
                "confirmed": True,
                "bars_checked": result["bars_checked"],
                "details": result["details"],
            }
            confirmed.append(sig)
        else:
            sig["rejection"] = {
                "confirmed": False,
                "reason": result["reason"],
                "bars_checked": result["bars_checked"],
            }
            rejected.append(sig)

    return confirmed, rejected


if __name__ == "__main__":
    # Quick self-test: confirm a known BTC signal
    test_signal = {
        "ticker": "BTC",
        "direction": "long",
        "entry_price": 64000,
        "stop_price": 62000,
        "date": "2026-07-30",
    }

    print("Testing intraday confirmation on BTC...")
    result = confirm_signal(test_signal, verbose=True)

    print(f"\nResult: confirmed={result['confirmed']}")
    print(f"Reason: {result['reason']}")
    print(f"Bars checked: {result['bars_checked']}")
    if result["hourly_data"] is not None and not result["hourly_data"].empty:
        print(f"\nHourly data sample:")
        print(result["hourly_data"].tail(10))
