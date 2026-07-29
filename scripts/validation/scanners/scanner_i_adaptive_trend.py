#!/usr/bin/env python3
"""
scanner_i_adaptive_trend.py
===========================
HermesForge Phase 1A — Strategy I: AdaptiveTrend (Momentum + ATR Trailing Stop)

Based on: Bui & Nguyen (arXiv:2602.11708) "Systematic Trend-Following with
Adaptive Portfolio Construction: Enhancing Risk-Adjusted Alpha in
Cryptocurrency Markets"

Signal Rules:
  1. Compute momentum: MOM_t = (P_t - P_{t-L}) / P_{t-L}
  2. Long entry when MOM_t > theta_entry AND price > SMA200 (trend filter)
  3. Short entry when MOM_t < -theta_entry AND price < SMA200 (trend filter)
  4. Initial stop: ATR-based trailing (alpha * ATR)
  5. Exit: trailing stop hit (simulated forward)

Timeframe-agnostic: works on any OHLCV bars (6h, 8h, daily).
For Phase 1A, uses daily bars for both stocks and crypto.

Parameters optimized via grid sweep on 19-ticker sample (2026-07-26).
Sweep tested 320 combinations across L, theta, alpha, max_bars.
Best: L=10, theta=0.20, alpha=2.0, max_bars=120 with SMA200 trend filter.
  → avg_r=0.527 (up from 0.033 with fixed defaults), win_rate=48.3%

Dependencies: pandas, numpy only.
"""

import numpy as np
import pandas as pd

STRATEGY_ID = "I_ADAPTIVE_TREND"

# ── Parameters (Phase 1A — optimized via grid sweep 2026-07-26) ──────────────
LOOKBACK = 10                # momentum lookback (L) — swept from [10,20,30,50]
ENTRY_THRESHOLD = 0.20      # momentum threshold (theta_entry) — swept from [0.05..0.20]
ATR_PERIOD = 14              # ATR lookback (k)
ATR_MULTIPLIER = 2.0         # trailing stop multiplier (alpha) — swept from [2.0..3.5]
MIN_RR = 1.5                 # minimum R:R for signal reporting
MAX_BARS_HELD = 120          # time-stop (bars) — swept from [40..120]
TREND_FILTER_PERIOD = 200    # SMA period for trend filter (0 = disabled)
LONG_ONLY = True             # stocks: skip short entries (structural positive drift)


# ── Indicator helpers ────────────────────────────────────────────────────────

def _compute_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    """Average True Range over k periods.

    TR = max(high-low, |high-prev_close|, |low-prev_close|)
    ATR = Wilder's smoothing of TR (EMA with alpha=1/period).
    """
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    return atr


def _compute_momentum(close: pd.Series, lookback: int = LOOKBACK) -> pd.Series:
    """MOM_t = (P_t - P_{t-L}) / P_{t-L}"""
    return close.pct_change(periods=lookback)


# ── Exit simulation (trailing stop lifecycle) ────────────────────────────────

def _simulate_trailing_exit(
    df: pd.DataFrame,
    entry_idx: int,
    direction: str,
    entry_price: float,
    initial_stop: float,
    atr_series: pd.Series,
) -> tuple[float, str, int, float]:
    """
    Simulate the ATR trailing stop from entry_idx forward.

    For longs:
        S_t = max(S_{t-1}, P_t - alpha * ATR_t)
        Exit when P_t < S_t

    For shorts (symmetric):
        S_t = min(S_{t-1}, P_t + alpha * ATR_t)
        Exit when P_t > S_t

    Returns (exit_price, exit_reason, bars_held, final_stop).
    exit_reason is 'stop' or 'time'.
    """
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    atr_vals = atr_series.values

    alpha = ATR_MULTIPLIER
    n_bars = len(df)
    max_idx = min(entry_idx + MAX_BARS_HELD, n_bars - 1)

    if direction == "long":
        stop = initial_stop
        for i in range(entry_idx + 1, max_idx + 1):
            # Update trailing stop (monotonic — only moves up for longs)
            new_stop = max(stop, closes[i] - alpha * atr_vals[i])
            # Check if intrabar low pierced the stop
            if lows[i] <= stop:
                return stop, "stop", i - entry_idx, stop
            stop = new_stop
        return closes[max_idx], "time", max_idx - entry_idx, stop

    else:  # short
        stop = initial_stop
        for i in range(entry_idx + 1, max_idx + 1):
            # Update trailing stop (monotonic — only moves down for shorts)
            new_stop = min(stop, closes[i] + alpha * atr_vals[i])
            # Check if intrabar high pierced the stop
            if highs[i] >= stop:
                return stop, "stop", i - entry_idx, stop
            stop = new_stop
        return closes[max_idx], "time", max_idx - entry_idx, stop


# ── Main scan function ──────────────────────────────────────────────────────

def scan(df: pd.DataFrame, ticker: str = "") -> list[dict]:
    """
    Scan OHLCV data for AdaptiveTrend momentum + ATR trailing stop signals.

    Returns a list of signal dicts (one per entry signal found).
    Each dict contains: date, direction, entry_price, stop_price,
    target_price, r_multiple, momentum, atr_at_signal, etc.

    Only one position is open at a time per asset — new entries are
    blocked until the previous position exits (stop or time).

    The most recent signal (last in list) is the actionable one for
    daily publishing / paper trading.

    Trend filter: when TREND_FILTER_PERIOD > 0, long entries require
    price above SMA(period), short entries require price below SMA(period).
    This eliminates counter-trend signals that dominated the original
    fixed-parameter version (shorts were avg R = -0.149 without filter).
    """
    min_len = LOOKBACK + ATR_PERIOD + 1
    if TREND_FILTER_PERIOD > 0:
        min_len = max(min_len, TREND_FILTER_PERIOD + 1)
    if len(df) < min_len:
        return []

    close = df["close"]
    mom = _compute_momentum(close, LOOKBACK)
    atr = _compute_atr(df, ATR_PERIOD)
    sma_trend = close.rolling(TREND_FILTER_PERIOD, min_periods=50).mean() if TREND_FILTER_PERIOD > 0 else None

    signals = []
    n = len(df)
    next_allowed_entry = 0  # track when a new entry is allowed (after exit)

    start_idx = LOOKBACK + ATR_PERIOD
    if sma_trend is not None:
        start_idx = max(start_idx, TREND_FILTER_PERIOD)

    for i in range(start_idx, n - 1):
        # Skip if a position is still open
        if i < next_allowed_entry:
            continue

        mom_val = mom.iloc[i]
        if np.isnan(mom_val) or np.isnan(atr.iloc[i]):
            continue

        # Trend filter: only long above SMA, short below
        if sma_trend is not None:
            sv = sma_trend.iloc[i]
            if np.isnan(sv):
                continue
            price_above_trend = close.iloc[i] > sv

        # Entry conditions (with trend filter)
        if mom_val > ENTRY_THRESHOLD:
            if sma_trend is not None and not price_above_trend:
                continue
            direction = "long"
        elif mom_val < -ENTRY_THRESHOLD:
            if LONG_ONLY:
                continue  # skip shorts on stocks (structural positive drift)
            if sma_trend is not None and price_above_trend:
                continue
            direction = "short"
        else:
            continue

        entry_price = close.iloc[i]
        atr_val = atr.iloc[i]

        if direction == "long":
            initial_stop = entry_price - ATR_MULTIPLIER * atr_val
        else:
            initial_stop = entry_price + ATR_MULTIPLIER * atr_val

        # Simulate the trailing stop exit
        try:
            exit_price, exit_reason, bars_held, final_stop = _simulate_trailing_exit(
                df, i, direction, entry_price, initial_stop, atr
            )
        except Exception:
            continue

        # Block re-entry until after this position exits
        exit_idx = i + bars_held
        next_allowed_entry = exit_idx + 1

        # Guard against NaN from edge cases
        if np.isnan(exit_price) or np.isnan(final_stop):
            continue

        # Calculate realized R:R
        if direction == "long":
            risk = entry_price - initial_stop
            reward = exit_price - entry_price
        else:
            risk = initial_stop - entry_price
            reward = entry_price - exit_price

        if risk <= 0 or np.isnan(risk) or np.isnan(reward) or np.isnan(exit_price):
            continue

        r_multiple = reward / risk

        # Notional target for R:R reporting (3x momentum projection)
        if direction == "long":
            target_price = entry_price * (1 + abs(mom_val) * 3)
        else:
            target_price = entry_price * (1 - abs(mom_val) * 3)

        # Subperiod label (for stock/crypto context)
        subperiod = df["subperiod"].iloc[i] if "subperiod" in df.columns else "n/a"

        signals.append({
            "date": df.index[i],
            "ticker": ticker,
            "direction": direction,
            "entry_price": round(entry_price, 6),
            "stop_price": round(initial_stop, 6),
            "target_price": round(target_price, 6),
            "exit_price": round(exit_price, 6),
            "exit_reason": exit_reason,
            "bars_held": bars_held,
            "r_multiple": round(r_multiple, 2),
            "momentum": round(float(mom_val), 4),
            "atr_at_signal": round(float(atr_val), 6),
            "atr_multiplier": ATR_MULTIPLIER,
            "final_stop": round(final_stop, 6),
            "lookback": LOOKBACK,
            "entry_threshold": ENTRY_THRESHOLD,
            "subperiod": subperiod,
            "confirmation_level": "Level 1",
            "strategy_id": "STR-I-adaptive-trend",
        })

    return signals


if __name__ == "__main__":
    # Quick test: scan BTC daily data
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "paper_trading"))
    from fetch_crypto_data import load_all

    data = load_all()
    if "BTC" in data:
        sigs = scan(data["BTC"], "BTC")
        print(f"BTC: {len(sigs)} signals found over {len(data['BTC'])} bars")
        wins = [s for s in sigs if s["r_multiple"] > 0]
        losses = [s for s in sigs if s["r_multiple"] <= 0]
        print(f"  Wins: {len(wins)}  Losses: {len(losses)}  Win rate: {len(wins)/len(sigs)*100:.1f}%" if sigs else "  No signals")
        print(f"  Avg R: {np.mean([s['r_multiple'] for s in sigs]):.2f}" if sigs else "")
        print(f"\nLast 5 signals:")
        for s in sigs[-5:]:
            print(f"  {s['date'].date()} {s['direction']:5s} entry={s['entry_price']:10.2f} "
                  f"exit={s['exit_price']:10.2f} R={s['r_multiple']:+.2f} "
                  f"({s['exit_reason']}, {s['bars_held']} bars) mom={s['momentum']:+.3f}")
