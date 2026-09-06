#!/usr/bin/env python3
"""
scanner_btc_supply_crunch.py — STR-20260906-BTC-SUPPLY-CRUNCH

Edge candidate: CAND-20260906-btc-supply-crunch-institutional-floor
Source hypothesis: BTC is in a supply crunch regime where institutional ETF
inflows create a price floor, but thin spot volume creates a fragile structure.
The most probable resolution is an asymmetric breakout above $80K, with the
size of the move proportional to how long the squeeze builds.

Signal Rules (batch / cross-sectional, crypto only):
  1. BTC must be in a "compression zone": 20-day price range width below
     COMPRESSION_THRESHOLD (narrow consolidation).
  2. BTC spot volume must be below THIN_VOLUME_PCT percentile of its 20-day
     history (confirming thin float / low liquidity).
  3. BTC must be above its 50-day SMA (uptrend / institutional floor intact).
  4. Entry: LONG at close when all conditions met.
  5. Exit: ATR-based trailing stop or MIN_RR target, max MAX_BARS_HELD.

Data sources:
  - BTC-USD from the crypto data dict (Hyperliquid daily OHLCV, 2020+).
  - No external ETF flow data needed — the supply-crunch proxy is
    compression + thin volume + uptrend.

NOTE on scope: The full edge requires real-time ETF flow data
(CoinGlass/The Block) which is not cached in this repo. The proxy above
tests the testable core: "compressed BTC with low volume in an uptrend
tends to break out asymmetrically to the upside."

Dependencies: pandas, numpy.
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "STR-20260906-BTC-SUPPLY-CRUNCH"

# ── Parameters (module-level; walk-forward monkey-patches these) ─────────────
LOOKBACK = 20               # Rolling window for volume percentile & range
THIN_VOLUME_PCT = 50        # Volume < this percentile = thin float (relaxed from 25)
COMPRESSION_THRESHOLD = 0.15  # 20-day range (high-low)/close < this = compressed (relaxed from 0.08)
SMA_PERIOD = 50             # Minimum trend filter
ATR_PERIOD = 14
ATR_STOP_MULT = 2.5         # Stop = entry - ATR_STOP_MULT * ATR (relaxed from 2.0)
MIN_RR = 1.5                # Minimum reward-to-risk ratio for target (relaxed from 2.0)
MAX_BARS_HELD = 15          # ~3 weeks maximum hold
MIN_HISTORY = 60            # Need >= this many bars before generating signals
REENTRY_COOLDOWN = 5        # Min bars between signals for BTC (relaxed from 10)


def _subperiod(date) -> str:
    if pd.isna(date):
        return "unknown"
    d = date.date() if hasattr(date, "date") else date
    if d < pd.Timestamp("2020-08-19").date():
        return "pre_warmup"
    if d <= pd.Timestamp("2021-12-31").date():
        return "period1_bull"
    if d <= pd.Timestamp("2023-12-31").date():
        return "period2_bear"
    return "period3_current"


def _compute_atr(high, low, close, period=ATR_PERIOD):
    prior_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prior_close).abs(),
        (low - prior_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _simulate_exit(closes: np.ndarray, entry_idx: int, entry_price: float,
                   stop_price: float, target_price: float,
                   direction: str = "long", max_bars: int = MAX_BARS_HELD):
    """Simulate forward exit: stop, target, or time."""
    n = len(closes)
    for offset in range(1, max_bars + 1):
        idx = entry_idx + offset
        if idx >= n:
            last = n - 1
            return closes[last], "time", offset - 1
        c = float(closes[idx])
        if direction == "long":
            if c >= target_price:
                return c, "target", offset
            if c <= stop_price:
                return c, "stop", offset
        else:
            if c <= target_price:
                return c, "target", offset
            if c >= stop_price:
                return c, "stop", offset
    exit_idx = min(entry_idx + max_bars, n - 1)
    return float(closes[exit_idx]), "time", max_bars


def scan(data_dict: dict) -> list:
    """Batch scanner for the BTC supply crunch / thin-float breakout edge.

    Args:
        data_dict: {ticker: DataFrame} of crypto OHLCV (daily). Must
        include "BTC" or a close variant (e.g., "BTC-USD").

    Returns:
        list of signal dicts, one per completed trade.
    """
    if not data_dict:
        return []

    # Find BTC in the data dict
    btc_key = None
    for k in data_dict.keys():
        k_up = k.upper().replace("-", "").replace(" ", "")
        if k_up in ("BTC", "BTCUSD", "BTCUSDT", "BITCOIN"):
            btc_key = k
            break
    if btc_key is None:
        return []

    df = data_dict[btc_key].copy()
    df.columns = [c.lower() for c in df.columns]
    df.sort_index(inplace=True)

    # Standardise OHLCV column names
    close = df["close"] if "close" in df.columns else df.iloc[:, 3]
    high = df["high"] if "high" in df.columns else df.iloc[:, 1]
    low = df["low"] if "low" in df.columns else df.iloc[:, 2]
    volume = df["volume"] if "volume" in df.columns else df.iloc[:, 5]

    if len(df) < MIN_HISTORY:
        return []

    # ── Compute indicators ─────────────────────────────────────────────────
    close_arr = close.values.astype(float)
    high_arr = high.values.astype(float)
    low_arr = low.values.astype(float)
    volume_arr = volume.values.astype(float)

    # 50-day SMA
    sma50 = close.rolling(SMA_PERIOD, min_periods=SMA_PERIOD).mean()

    # 20-day volume percentile
    vol_rank = volume.rolling(LOOKBACK, min_periods=LOOKBACK).rank(pct=True)

    # 20-day price range width (H-L)/C
    range_width = (high.rolling(LOOKBACK, min_periods=LOOKBACK).max()
                   - low.rolling(LOOKBACK, min_periods=LOOKBACK).min()) / close

    # ATR
    atr_series = _compute_atr(high, low, close, period=ATR_PERIOD)

    # ── Scan for signals ───────────────────────────────────────────────────
    signals = []
    last_signal_idx = -REENTRY_COOLDOWN - 1  # allow first signal immediately

    n = len(df)
    min_start = max(SMA_PERIOD, LOOKBACK, ATR_PERIOD) + 2

    for i in range(min_start, n):
        # Check all conditions
        if pd.isna(sma50.iloc[i]):
            continue
        if pd.isna(vol_rank.iloc[i]):
            continue
        if pd.isna(range_width.iloc[i]):
            continue
        if pd.isna(atr_series.iloc[i]):
            continue

        # Condition 1: Price above 50-day SMA (uptrend intact)
        if close_arr[i] < sma50.iloc[i]:
            continue

        # Condition 2: Volume below thin percentile
        if vol_rank.iloc[i] * 100 > THIN_VOLUME_PCT:
            continue

        # Condition 3: Price range is compressed
        if range_width.iloc[i] > COMPRESSION_THRESHOLD:
            continue

        # Condition 4: ATR is valid
        atr_val = float(atr_series.iloc[i])
        if atr_val <= 0 or np.isnan(atr_val):
            continue

        # Cooldown check
        bars_since_last = i - last_signal_idx
        if bars_since_last < REENTRY_COOLDOWN:
            continue

        # Enter LONG
        entry_price = close_arr[i]
        atr_val = float(atr_series.iloc[i])
        stop_price = entry_price - ATR_STOP_MULT * atr_val
        risk = entry_price - stop_price
        if risk <= 0 or risk / entry_price < 0.002:
            continue
        target_price = entry_price + MIN_RR * risk

        # Simulate exit forward
        ep, er, bh = _simulate_exit(
            close_arr, i, entry_price, stop_price, target_price, "long"
        )
        r_mult = (ep - entry_price) / risk

        ts = pd.Timestamp(df.index[i])
        signals.append({
            "ticker": btc_key,
            "date": ts.date(),
            "direction": "long",
            "entry_price": round(float(entry_price), 2),
            "stop_price": round(float(stop_price), 2),
            "target_price": round(float(target_price), 2),
            "exit_price": round(float(ep), 2),
            "exit_reason": er,
            "r_multiple": round(float(r_mult), 4),
            "bars_held": int(bh),
            "subperiod": _subperiod(ts),
            "strategy_id": STRATEGY_ID,
            "regime": "supply_crunch",
            "entry_type": "compression_breakout_long",
        })

        last_signal_idx = i

    return signals


# ── Smoke test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from fetch_data import load_all as load_stocks
    from pathlib import Path as _P

    # Try loading crypto data
    try:
        sys.path.insert(0, str(_P.home() / "HermesForge" / "scripts" / "paper_trading"))
        from fetch_crypto_data import load_all as load_crypto
        data = load_crypto()
        print(f"Loaded {len(data)} crypto tickers")
    except Exception as e:
        print(f"[INFO] Crypto data not available ({e}), trying stock universe for BTC...")
        data = load_stocks()
        print(f"Loaded {len(data)} stock tickers")

    if not data:
        print("No data loaded. Run the fetcher first.")
        sys.exit(1)

    sigs = scan(data)
    print(f"\nBTC Supply Crunch signals: {len(sigs)}")
    if sigs:
        r_vals = [s["r_multiple"] for s in sigs]
        wins = [s for s in sigs if s["r_multiple"] > 0]
        print(f"  Avg R: {np.mean(r_vals):+.4f}")
        print(f"  Win rate: {len(wins) / len(sigs):.1%}")
        print(f"  Median R: {np.median(r_vals):+.4f}")
        print(f"\nFirst 3 signals:")
        for sig in sigs[:3]:
            print(f"  {sig['date']} | Entry ${sig['entry_price']:.2f} | "
                  f"Exit ${sig['exit_price']:.2f} | R={sig['r_multiple']:+.4f} | "
                  f"Reason: {sig['exit_reason']}")
    else:
        print("No signals generated — check if BTC data is available.")