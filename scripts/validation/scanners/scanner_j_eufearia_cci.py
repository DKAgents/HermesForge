#!/usr/bin/env python3
"""
scanner_j_eufearia_cci.py
=========================
HermesForge Phase 1A — Strategy J: EUFEARIA CCI Reversal

Based on: EUFEARIA PRO 7 Pine Script by Philip Paul
Core: Modified CCI (Commodity Channel Index) with EMA smoothing + signal line crossover at extremes.

Indicator construction:
  1. avg_price = hlc3 = (high + low + close) / 3
  2. ema_esa = EMA(avg_price, channel_length=10)
  3. diff = EMA(|avg_price - ema_esa|, channel_length=10)
  4. ci = (avg_price - ema_esa) / (0.015 * diff)   [CCI formula with EMA]
  5. osc = EMA(ci, signal_length=21)
  6. sig = SMA(osc, 4)

Entry rules:
  Long:  osc crosses above sig AND osc <= -50 AND (strict: sig <= -50)
  Short: osc crosses below sig AND osc >= +50 AND (strict: sig >= +50)

Exit: ATR-based stop (1.0 ATR), time stop (10 bars), R:R target (2:1 min)
"""

import numpy as np
import pandas as pd

STRATEGY_ID = "J_EUFEARIA_CCI"

# ── Parameters (from Pine Script defaults) ───────────────────────────────────
CHANNEL_LENGTH = 10        # EMA period for CCI mean
SIGNAL_LENGTH = 21         # EMA period for oscillator smoothing
SIGNAL_LINE_PERIOD = 4     # SMA period for signal line
OB_LEVEL = 50              # Overbought threshold
OS_LEVEL = -50             # Oversold threshold
STRICT_EXTREME = True      # Require both osc + sig at extreme
ATR_PERIOD = 14
ATR_STOP_MULTIPLIER = 1.0  # Stop distance in ATR
MAX_BARS_HELD = 10         # Time stop
MIN_RR = 2.0               # Minimum reward:risk
CCI_CONSTANT = 0.015       # Lambert's constant


# ── Indicator helpers ────────────────────────────────────────────────────────

def _compute_hlc3(df: pd.DataFrame) -> pd.Series:
    """Typical price = (high + low + close) / 3"""
    return (df["high"] + df["low"] + df["close"]) / 3.0


def _compute_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    """Average True Range (Wilder's smoothing)."""
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _compute_eufearia_oscillator(df: pd.DataFrame,
                                  channel_len: int = CHANNEL_LENGTH,
                                  signal_len: int = SIGNAL_LENGTH,
                                  sig_period: int = SIGNAL_LINE_PERIOD) -> tuple[pd.Series, pd.Series]:
    """
    Compute the EUFEARIA PRO 7 oscillator and signal line.

    Returns (osc, sig) where:
      osc = EMA(CCI_modified, signal_len)
      sig = SMA(osc, sig_period)
    """
    hlc3 = _compute_hlc3(df)

    # Step 2: EMA of typical price
    ema_esa = hlc3.ewm(span=channel_len, adjust=False).mean()

    # Step 3: EMA of absolute deviation
    abs_dev = (hlc3 - ema_esa).abs()
    diff = abs_dev.ewm(span=channel_len, adjust=False).mean()

    # Step 4: CCI formula (with EMA, not SMA)
    # Guard against division by zero
    diff_safe = diff.replace(0, np.nan)
    ci = (hlc3 - ema_esa) / (CCI_CONSTANT * diff_safe)

    # Step 5: Oscillator = EMA of CCI
    osc = ci.ewm(span=signal_len, adjust=False).mean()

    # Step 6: Signal line = SMA of oscillator
    sig = osc.rolling(sig_period, min_periods=1).mean()

    return osc, sig


def _detect_crossover(osc: pd.Series, sig: pd.Series) -> pd.Series:
    """Detect when osc crosses above sig (returns 1) or below (returns -1). 0 = no cross."""
    above = osc > sig
    below = osc < sig
    prev_above = above.shift(1).fillna(False)
    prev_below = below.shift(1).fillna(False)

    cross_up = above & prev_below    # was below, now above → bullish crossover
    cross_down = below & prev_above  # was above, now below → bearish crossunder

    result = pd.Series(0, index=osc.index)
    result[cross_up] = 1
    result[cross_down] = -1
    return result


# ── Exit simulation ──────────────────────────────────────────────────────────

def _simulate_exit(df: pd.DataFrame, entry_idx: int, direction: str,
                   entry_price: float, stop_price: float,
                   target_price: float, max_bars: int = MAX_BARS_HELD) -> tuple[float, str, int]:
    """
    Simulate position exit. Returns (exit_price, exit_reason, bars_held).
    Checks stop, target, and time stop on each subsequent bar.
    """
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    n_bars = len(df)
    max_idx = min(entry_idx + max_bars, n_bars - 1)

    for i in range(entry_idx + 1, max_idx + 1):
        if direction == "long":
            # Check stop first (worst case)
            if lows[i] <= stop_price:
                return stop_price, "stop", i - entry_idx
            # Check target
            if highs[i] >= target_price:
                return target_price, "target", i - entry_idx
        else:  # short
            if highs[i] >= stop_price:
                return stop_price, "stop", i - entry_idx
            if lows[i] <= target_price:
                return target_price, "target", i - entry_idx

    # Time stop — exit at close
    return closes[max_idx], "time", max_idx - entry_idx


# ── Main scan function ──────────────────────────────────────────────────────

def scan(df: pd.DataFrame, ticker: str = "") -> list[dict]:
    """
    Scan OHLCV data for EUFEARIA CCI reversal signals.

    Returns list of signal dicts with entry, exit, and R-multiple for each trade.
    Only one position open at a time per asset.
    """
    min_len = max(CHANNEL_LENGTH, SIGNAL_LENGTH, ATR_PERIOD) + SIGNAL_LINE_PERIOD + 5
    if len(df) < min_len:
        return []

    osc, sig = _compute_eufearia_oscillator(df)
    atr = _compute_atr(df)
    crosses = _detect_crossover(osc, sig)

    signals = []
    n = len(df)
    next_allowed_entry = 0

    for i in range(min_len, n - 1):
        if i < next_allowed_entry:
            continue

        cross = crosses.iloc[i]
        if cross == 0:
            continue

        osc_val = osc.iloc[i]
        sig_val = sig.iloc[i]
        atr_val = atr.iloc[i]

        if np.isnan(osc_val) or np.isnan(sig_val) or np.isnan(atr_val):
            continue

        direction = None

        if cross == 1:  # bullish crossover
            # Long entry: osc crosses above sig at oversold
            if osc_val <= OS_LEVEL:
                if STRICT_EXTREME and sig_val > OS_LEVEL:
                    continue  # signal line not at extreme
                direction = "long"
        elif cross == -1:  # bearish crossunder
            # Short entry: osc crosses below sig at overbought
            if osc_val >= OB_LEVEL:
                if STRICT_EXTREME and sig_val < OB_LEVEL:
                    continue
                direction = "short"

        if direction is None:
            continue

        entry_price = df["close"].iloc[i]

        if direction == "long":
            stop_price = entry_price - ATR_STOP_MULTIPLIER * atr_val
            # Target: mean reversion toward zero line
            # Estimate price move based on oscillator distance from zero
            reversion_pct = abs(osc_val) / 100.0  # simplified
            target_price = entry_price * (1 + min(reversion_pct, 0.15))  # cap at 15%
        else:
            stop_price = entry_price + ATR_STOP_MULTIPLIER * atr_val
            reversion_pct = abs(osc_val) / 100.0
            target_price = entry_price * (1 - min(reversion_pct, 0.15))

        risk = abs(entry_price - stop_price)
        reward = abs(target_price - entry_price)

        if risk <= 0:
            continue

        rr = reward / risk
        if rr < MIN_RR:
            continue  # skip low R:R signals

        # Simulate exit
        try:
            exit_price, exit_reason, bars_held = _simulate_exit(
                df, i, direction, entry_price, stop_price, target_price
            )
        except Exception:
            continue

        next_allowed_entry = i + bars_held + 1

        # Calculate realized R-multiple
        if direction == "long":
            realized_r = (exit_price - entry_price) / risk
        else:
            realized_r = (entry_price - exit_price) / risk

        if np.isnan(realized_r):
            continue

        subperiod = df["subperiod"].iloc[i] if "subperiod" in df.columns else "n/a"

        signals.append({
            "date": df.index[i],
            "ticker": ticker,
            "direction": direction,
            "entry_price": round(entry_price, 6),
            "stop_price": round(stop_price, 6),
            "target_price": round(target_price, 6),
            "exit_price": round(exit_price, 6),
            "exit_reason": exit_reason,
            "bars_held": bars_held,
            "r_multiple": round(realized_r, 2),
            "osc_value": round(float(osc_val), 2),
            "sig_value": round(float(sig_val), 2),
            "atr_at_signal": round(float(atr_val), 6),
            "rr_projected": round(rr, 2),
            "subperiod": subperiod,
            "strategy_id": "STR-J-eufearia-cci",
        })

    return signals


if __name__ == "__main__":
    # Quick test on cached data
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from fetch_data import load_all

    data = load_all()
    if data:
        # Test on first few tickers
        test_tickers = list(data.keys())[:5]
        for ticker in test_tickers:
            sigs = scan(data[ticker], ticker)
            if sigs:
                wins = [s for s in sigs if s["r_multiple"] > 0]
                avg_r = np.mean([s["r_multiple"] for s in sigs])
                print(f"{ticker}: {len(sigs)} signals, {len(wins)} wins ({len(wins)/len(sigs)*100:.0f}%), avg R {avg_r:.2f}")
            else:
                print(f"{ticker}: 0 signals")
