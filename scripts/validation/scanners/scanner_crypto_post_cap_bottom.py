#!/usr/bin/env python3
"""scanner_crypto_post_cap_bottom.py -- STR-CAP-BOTTOM: Crypto Post-Capitulation Bounce.

Edge candidate: CAND-20260917-crypto-post-cap-bottom
Source hypothesis: BTC's dual-catalyst capitulation (CLARITY failure + Fed hike)
created a tactical bottom setup. After a 4%+ single-day drop with elevated volume,
BTC tends to mean-revert 5-8% within 10 trading days.

Generalized mechanical hypothesis:
  When BTC (or a major crypto) experiences a capitulation-sized daily decline
  (>= 4% drop) on volume at least 1.5x the 20-day average, the asset tends to
  bounce at least 40% of the drop distance within 10 bars. The edge is strongest
  in established uptrends (price above 200-day SMA) where the drop is a
  correction, not a trend change.

Signal Rules:
  Entry: daily close after >= 4% single-day drop AND volume >= 1.5x 20-day avg.
  Direction: Long only.
  Stop:  Entry - 1.5 * ATR(14)
  Target: Entry + (drop_pct * 0.40 * entry)
  Time stop: 10 bars max
  Uptrend filter: Price > 200-day SMA

Dependencies: pandas, numpy. Uses Hyperliquid crypto OHLC (via
fetch_crypto_data.load_all).
"""

import numpy as np
import pandas as pd

STRATEGY_ID = "STR-CAP-BOTTOM-CRYPTO-CAPITULATION-BOUNCE"

# Parameters (module-level so walk-forward can monkey-patch)
DROP_PCT = 0.04
VOLUME_MULT = 1.5
ATR_PERIOD = 14
ATR_STOP_MULT = 1.5
RECOVERY_FRACTION = 0.40
MAX_BARS_HELD = 10
MIN_HISTORY = 250
MIN_DROP_AMOUNT = 0.015

USE_UPTREND_FILTER = True
TREND_SMA = 200

ALLOWED_TICKERS = {"BTC", "ETH", "SOL"}


def _compute_atr(high, low, close, period=ATR_PERIOD):
    prior_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prior_close).abs(),
        (low - prior_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _subperiod(date) -> str:
    if pd.isna(date):
        return "unknown"
    return "crypto_unlabeled"


def scan(data_dict: dict) -> list:
    """Batch scan: crypto capitulation bounce (BTC/ETH/SOL)."""
    signals = []

    if not data_dict:
        return signals

    for ticker in ALLOWED_TICKERS:
        if ticker not in data_dict:
            continue

        df = data_dict[ticker].copy().sort_index()
        if len(df) < MIN_HISTORY:
            continue

        close = df["close"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        volume = df["volume"].astype(float) if "volume" in df.columns else pd.Series(1.0, index=df.index)

        # Indicators
        atr = _compute_atr(high, low, close)
        sma_200 = close.rolling(TREND_SMA, min_periods=TREND_SMA).mean()
        vol_sma_20 = volume.rolling(20, min_periods=20).mean()

        daily_drop = close.pct_change()

        dates = df.index
        close_arr = close.values
        high_arr = high.values
        low_arr = low.values
        volume_arr = volume.values
        atr_arr = atr.values
        sma_200_arr = sma_200.values
        vol_sma_arr = vol_sma_20.values
        drop_arr = daily_drop.values

        n = len(df)
        open_pos = None

        for i in range(n):
            date = dates[i]
            cp = float(close_arr[i])
            vol = float(volume_arr[i])

            if np.isnan(atr_arr[i]) or np.isnan(sma_200_arr[i]) or np.isnan(vol_sma_arr[i]):
                continue

            atr_val = float(atr_arr[i])
            sma_200_val = float(sma_200_arr[i])
            vol_sma_val = float(vol_sma_arr[i])

            # Manage open position
            if open_pos is not None:
                pos = open_pos
                bars_held = i - pos["entry_idx"]
                entry_price = pos["entry_price"]

                exit_reason = None
                exit_price = cp

                if cp <= pos["stop_price"]:
                    exit_reason = "stop"
                elif cp >= pos["target_price"]:
                    exit_reason = "target"
                elif bars_held >= MAX_BARS_HELD:
                    exit_reason = "time"

                if exit_reason is not None:
                    risk = entry_price - pos["stop_price"]
                    realised_r = (cp - entry_price) / risk if risk > 0 else 0.0

                    signals.append({
                        "ticker": ticker,
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
                        "drop_pct": round(float(pos.get("drop_pct", 0)), 4),
                        "vol_ratio": round(float(pos.get("vol_ratio", 0)), 2),
                    })
                    open_pos = None

            # Look for new entry
            if open_pos is not None:
                continue

            # Entry condition 1: significant drop today
            drop_today = float(drop_arr[i]) if not pd.isna(drop_arr[i]) else 0.0
            if drop_today >= -MIN_DROP_AMOUNT or drop_today > -DROP_PCT:
                continue

            # Entry condition 2: elevated volume
            if vol_sma_val > 0 and vol < VOLUME_MULT * vol_sma_val:
                continue

            # Entry condition 3: above 200-day SMA (uptrend filter)
            if USE_UPTREND_FILTER and sma_200_val > 0 and cp < sma_200_val:
                continue

            # Entry condition 4: valid ATR
            if atr_val <= 0:
                continue

            drop_pct = abs(drop_today)
            stop_price = cp - ATR_STOP_MULT * atr_val
            risk = cp - stop_price
            if risk <= 0:
                continue

            target_price = cp + RECOVERY_FRACTION * drop_pct * cp

            min_rr = 1.0
            if target_price - cp < min_rr * risk:
                target_price = cp + min_rr * risk

            vol_ratio = vol / vol_sma_val if vol_sma_val > 0 else 0.0

            open_pos = {
                "entry_idx": i,
                "entry_price": cp,
                "stop_price": stop_price,
                "target_price": target_price,
                "entry_date": date,
                "drop_pct": drop_pct,
                "vol_ratio": vol_ratio,
            }

        # Force-close any still-open position at last available close
        if open_pos is not None:
            pos = open_pos
            j = n - 1
            cp = float(close_arr[j])
            risk = pos["entry_price"] - pos["stop_price"]
            realised_r = (cp - pos["entry_price"]) / risk if risk > 0 else 0.0
            signals.append({
                "ticker": ticker,
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
                "drop_pct": round(float(pos.get("drop_pct", 0)), 4),
                "vol_ratio": round(float(pos.get("vol_ratio", 0)), 2),
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
    print(f"\nRunning {STRATEGY_ID}: crypto capitulation bounce...")
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