#!/usr/bin/env python3
"""
scanner_crypto_op_mean_reversion.py — STR-OP-MR: OP Mean Reversion Bounce

Edge candidate: CAND-20260830-crypto-mean-reversion
Source hypothesis: "Short-term oversold in uptrend. Buy OP for mean reversion
bounce. Typical recovery: 30-50% of the 7d drop within 3-5 days."

Signal Rules:
  Entry: OP daily RSI(14) < 35 AND close within 2% of 20-day SMA (near 20MA).
  Stop:  Below recent 10-day swing low.
  Target: 50% of the 7-day drop recovered (entry + 0.5 * recent_drop).
  Time stop: Max 5 bars held.

  Exit (first triggers):
    1. Price >= target_price  (50% recovery of the 7d drawdown)
    2. RSI(14) > 60           (oversold bounce complete)
    3. Bars held >= MAX_BARS_HELD (5 bars time stop)
    4. Price <= stop_price    (stop loss hit)

Dependencies: pandas, numpy. Uses Hyperliquid crypto OHLC (via
fetch_crypto_data.load_all).

Survivorship-bias caveat: Single-asset OP — no cross-sectional survivorship
concern, but OP may have been listed recently (2022+). Transaction costs NOT
modeled in Phase 1A; walk-forward applies spread+commission.
"""

import numpy as np
import pandas as pd

STRATEGY_ID = "STR-OP-MR-CRYPTO-MEAN-REVERSION"

# ── Parameters (module-level so walk-forward can monkey-patch) ───────────────
RSI_ENTRY = 35            # Enter when RSI < this
SMA_PERIOD = 20           # 20-day moving average
SMA_TOLERANCE = 0.02      # Close must be within 2% of SMA (above or below)
SWING_LOOKBACK = 10       # Lookback for swing low (stop)
RSI_EXIT = 60             # Exit when RSI > this
MIN_RR = 1.0              # Minimum risk:reward (fallback if 7d drop is tiny)
MAX_BARS_HELD = 5         # Max bars time stop
MIN_HISTORY = 30          # Need >= this many bars for RSI/SMA to stabilize

# Allowed tickers for this strategy (single-asset focus)
ALLOWED_TICKERS = {"OP"}


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Compute RSI using Wilder's smoothing."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _subperiod(date) -> str:
    if pd.isna(date):
        return "unknown"
    return "crypto_unlabeled"


def scan(data_dict: dict) -> list:
    """Batch scan: OP mean reversion bounce (single-asset).

    Args:
        data_dict: {ticker: DataFrame} of crypto OHLCV (daily). Only OP is
        processed; other tickers are ignored.
    """
    signals = []

    if not data_dict:
        return signals

    # Only process OP
    if "OP" not in data_dict:
        return signals

    df = data_dict["OP"].copy().sort_index()
    if len(df) < MIN_HISTORY:
        return signals

    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)

    # Compute indicators
    rsi = _compute_rsi(close, 14)
    sma_20 = close.rolling(SMA_PERIOD, min_periods=SMA_PERIOD).mean()
    swing_low_10 = low.rolling(SWING_LOOKBACK, min_periods=SWING_LOOKBACK).min()

    # 7d drop amount = decline over last 7 days
    close_7d_ago = close.shift(7)
    seven_day_drop = close_7d_ago - close  # positive when price dropped
    # The high for the 7d period for recovery calc
    high_7d = close_7d_ago  # use close 7d ago as the "high before drop" proxy

    dates = df.index
    close_arr = close.values
    rsi_arr = rsi.values
    sma_arr = sma_20.values
    swing_low_arr = swing_low_10.values
    seven_day_drop_arr = seven_day_drop.values
    high_7d_arr = high_7d.values

    n = len(df)
    # Track open position state (single-asset, at most one position at a time)
    open_pos = None  # dict with entry_idx, entry_price, stop, target, etc.

    for i in range(n):
        date = dates[i]
        if pd.isna(rsi_arr[i]) or pd.isna(sma_arr[i]) or pd.isna(swing_low_arr[i]):
            continue

        cp = float(close_arr[i])
        rsi_val = float(rsi_arr[i])
        sma_val = float(sma_arr[i])
        swing_low = float(swing_low_arr[i])

        # ── Manage open position ──
        if open_pos is not None:
            pos = open_pos
            bars_held = i - pos["entry_idx"]
            entry_price = pos["entry_price"]

            exit_reason = None
            exit_price = cp

            # Check exits
            if cp <= pos["stop_price"]:
                exit_reason = "stop"
            elif cp >= pos["target_price"]:
                exit_reason = "target"
            elif not np.isnan(rsi_val) and rsi_val >= RSI_EXIT:
                exit_reason = "rsi_exit"
            elif bars_held >= MAX_BARS_HELD:
                exit_reason = "time"

            if exit_reason is not None:
                risk = entry_price - pos["stop_price"]
                realised_r = (cp - entry_price) / risk if risk > 0 else 0.0

                signals.append({
                    "ticker": "OP",
                    "date": pos["entry_date"],
                    "direction": "long",
                    "entry_price": round(float(entry_price), 6),
                    "stop_price": round(float(pos["stop_price"]), 6),
                    "target_price": round(float(pos["target_price"]), 6),
                    "exit_price": round(float(exit_price), 6),
                    "exit_reason": exit_reason,
                    "r_multiple": round(float(realised_r), 4),
                    "bars_held": int(bars_held),
                    "subperiod": _subperiod(pos["entry_date"]),
                    "strategy_id": STRATEGY_ID,
                    "rsi_entry": round(float(pos.get("rsi_entry", 0)), 2),
                    "sma_pct": round(float(pos.get("sma_pct", 0)), 4),
                })
                open_pos = None

        # ── Look for new entry ──
        if open_pos is not None:
            continue  # already in a position

        # Entry conditions: RSI < 35 AND close near 20MA
        if np.isnan(rsi_val) or np.isnan(sma_val):
            continue
        if rsi_val >= RSI_ENTRY:
            continue

        # Check proximity to SMA (within 2%)
        if sma_val <= 0:
            continue
        sma_pct_diff = (cp - sma_val) / sma_val
        if abs(sma_pct_diff) > SMA_TOLERANCE:
            continue

        # Compute stop and target
        stop_price = swing_low
        if stop_price <= 0 or cp <= stop_price:
            continue

        risk = cp - stop_price

        # Target: 50% of the 7-day drop recovery
        drop_val = float(seven_day_drop_arr[i]) if not pd.isna(seven_day_drop_arr[i]) else 0.0
        if drop_val > 0:
            target_price = cp + 0.5 * drop_val
        else:
            # Fallback: use MIN_RR
            target_price = cp + MIN_RR * risk

        # Ensure target is at least MIN_RR
        if target_price < cp + MIN_RR * risk:
            target_price = cp + MIN_RR * risk

        open_pos = {
            "entry_idx": i,
            "entry_price": cp,
            "stop_price": stop_price,
            "target_price": target_price,
            "entry_date": date,
            "rsi_entry": rsi_val,
            "sma_pct": sma_pct_diff,
        }

    # ── Force-close any still-open position at last available close ──
    if open_pos is not None:
        pos = open_pos
        j = n - 1
        cp = float(close_arr[j])
        risk = pos["entry_price"] - pos["stop_price"]
        realised_r = (cp - pos["entry_price"]) / risk if risk > 0 else 0.0
        signals.append({
            "ticker": "OP",
            "date": pos["entry_date"],
            "direction": "long",
            "entry_price": round(float(pos["entry_price"]), 6),
            "stop_price": round(float(pos["stop_price"]), 6),
            "target_price": round(float(pos["target_price"]), 6),
            "exit_price": round(float(cp), 6),
            "exit_reason": "end_of_data",
            "r_multiple": round(float(realised_r), 4),
            "bars_held": int(j - pos["entry_idx"]),
            "subperiod": _subperiod(pos["entry_date"]),
            "strategy_id": STRATEGY_ID,
            "rsi_entry": round(float(pos.get("rsi_entry", 0)), 2),
            "sma_pct": round(float(pos.get("sma_pct", 0)), 4),
        })

    return signals


if __name__ == "__main__":
    import sys
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / "paper_trading"))
    from fetch_crypto_data import load_all as load_all_crypto

    print("Loading crypto data...")
    crypto = load_all_crypto()
    print(f"  {len(crypto)} symbols loaded")

    print("\nRunning STR-OP-MR: OP mean reversion...")
    sigs = scan(crypto)

    if not sigs:
        print("No signals generated.")
        sys.exit(0)

    r_values = [s["r_multiple"] for s in sigs]
    wins = [s for s in sigs if s["r_multiple"] > 0]
    avg_r = np.mean(r_values)
    win_rate = len(wins) / len(sigs)

    print(f"\nResults ({STRATEGY_ID}):")
    print(f"  Signals: {len(sigs)}")
    print(f"  Avg R: {avg_r:+.4f}")
    print(f"  Win rate: {win_rate:.1%}")

    by_year = {}
    for s in sigs:
        yr = str(s["date"])[:4]
        if yr not in by_year:
            by_year[yr] = []
        by_year[yr].append(s["r_multiple"])
    print("  By year:")
    for yr in sorted(by_year.keys()):
        yr_r = by_year[yr]
        print(f"    {yr}: {len(yr_r):3d} sigs, avg R = {np.mean(yr_r):+.4f}")