"""
scanner_b_macd_divergence.py
============================
HermesForge Phase 1A — Strategy B: MACD Histogram Divergence

Signal Rules (bearish direction shown; bullish mirrors all conditions):

BEARISH (short signal — divergence in uptrend):
  Maturity gate : MACD line continuously above zero for >= 15 consecutive bars
  Stage 1       : price makes new 10-bar high AND histogram is narrowing
                  (|hist[i]| < |hist[i-1]| for >= 2 consecutive bars, hist > 0)
  Stage 2       : MACD line makes a lower high vs. reading 10-20 bars ago
                  (when the prior price swing high occurred)
  Entry trigger : MACD line crosses below signal line
                  (macd[i] < signal[i] AND macd[i-1] >= signal[i-1])
  Stop          : structure-based (nearest confirmed swing, ATR-capped at 2.0)
  Target        : nearest confirmed overhead/below resistance meeting min_rr=1.5
  Confirmation  : Level 2 if RSI >= 70, else Level 1

BULLISH (long signal — divergence in downtrend):
  Mirror of all conditions above.

v2.0 (US-115): Entry/stop/target now derived from the shared market_structure
module (pullback entry to confirmed support, structure stop, natural
resistance target). The MACD divergence detection logic is unchanged.

Exit simulation (same as Scanner A):
  target / stop / 8-bar time stop — whichever comes first.

Dependencies: pandas, numpy only.
"""

import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path

# Sibling import for market_structure module (same directory)
sys.path.insert(0, str(Path(__file__).parent))
from market_structure import compute_structure_trade

STRATEGY_ID      = "B_MACD_DIVERGENCE"
STRATEGY_VERSION = "2.0"
MACD_FAST        = 12
MACD_SLOW        = 26
MACD_SIGNAL      = 9
ATR_PERIOD       = 14
RSI_PERIOD       = 14
MATURITY_BARS    = 15    # consecutive bars MACD must stay same side of zero
NARROWING_BARS   = 2     # consecutive bars of narrowing histogram required
SWING_LOOKBACK   = 10    # bars for "new N-bar high/low" check
PRIOR_SWING_RANGE = (5, 60)  # wider lookback for Stage 2 prior swing (was 10-20, too narrow)
MAX_BARS_HELD    = 8
COOLDOWN_BARS    = 20    # per-ticker cooldown after an accepted trade
LIQUIDITY_FILTER_ENABLED = False  # Factor decomposition: less liquid = better signals (p=0.0025)
LIQUIDITY_MAX_DV_RANK    = 0.80   # Skip tickers above this percentile of 60d dollar volume
DV_LOOKBACK              = 60     # Dollar volume lookback period


# ---------------------------------------------------------------------------
# Indicator helpers
# ---------------------------------------------------------------------------

def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder-smoothed RSI (EWM, alpha = 1/period)."""
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs       = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _compute_macd(close: pd.Series) -> tuple:
    """
    Standard MACD via EWM.
    Returns (macd_line, signal_line, histogram) as pd.Series.
    """
    ema_fast   = close.ewm(span=MACD_FAST,   adjust=False).mean()
    ema_slow   = close.ewm(span=MACD_SLOW,   adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=MACD_SIGNAL, adjust=False).mean()
    histogram  = macd_line - signal_line
    return macd_line, signal_line, histogram


def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                 period: int = 14) -> pd.Series:
    """
    Average True Range (Wilder smoothing via EWM).
    TR = max(high-low, |high-prev_close|, |low-prev_close|)
    """
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


# ---------------------------------------------------------------------------
# Exit simulation helper
# ---------------------------------------------------------------------------

def _simulate_exit(
    closes: np.ndarray,
    entry_idx: int,
    entry_price: float,
    stop_price: float,
    target_price: float,
    direction: str,          # 'long' or 'short'
    max_bars: int = MAX_BARS_HELD,
) -> tuple:
    """
    Scan forward from bar after entry_idx for up to max_bars bars.
    For 'long'  : target = close >= target_price ; stop = close <= stop_price
    For 'short' : target = close <= target_price ; stop = close >= stop_price
    Returns (exit_price, exit_reason, bars_held).
    """
    n = len(closes)
    for offset in range(1, max_bars + 1):
        idx = entry_idx + offset
        if idx >= n:
            last = min(entry_idx + offset - 1, n - 1)
            return closes[last], "time", offset
        c = closes[idx]
        if direction == "long":
            if c >= target_price:
                return c, "target", offset
            if c <= stop_price:
                return c, "stop", offset
        else:  # short
            if c <= target_price:
                return c, "target", offset
            if c >= stop_price:
                return c, "stop", offset

    exit_idx = min(entry_idx + max_bars, n - 1)
    return closes[exit_idx], "time", max_bars


# ---------------------------------------------------------------------------
# Stage helpers
# ---------------------------------------------------------------------------

def _count_consecutive_above_zero(arr: np.ndarray, end_idx: int) -> int:
    """
    Count how many consecutive bars ending at end_idx (inclusive) have
    arr[j] > 0.
    """
    count = 0
    for j in range(end_idx, -1, -1):
        if arr[j] > 0:
            count += 1
        else:
            break
    return count


def _count_consecutive_below_zero(arr: np.ndarray, end_idx: int) -> int:
    """
    Count how many consecutive bars ending at end_idx (inclusive) have
    arr[j] < 0.
    """
    count = 0
    for j in range(end_idx, -1, -1):
        if arr[j] < 0:
            count += 1
        else:
            break
    return count


def _histogram_narrowing_count(hist_arr: np.ndarray, end_idx: int,
                                side: str) -> int:
    """
    Count consecutive bars of narrowing histogram magnitude ending at end_idx.
    side='bearish' : hist > 0 and |hist| decreasing
    side='bullish' : hist < 0 and |hist| decreasing (magnitude narrowing)
    Returns count (>= 0). 0 means condition not met at end_idx.
    """
    # First check the current bar is on the right side
    if side == "bearish" and hist_arr[end_idx] <= 0:
        return 0
    if side == "bullish" and hist_arr[end_idx] >= 0:
        return 0

    count = 0
    j = end_idx
    while j >= 1:
        curr_mag = abs(hist_arr[j])
        prev_mag = abs(hist_arr[j - 1])
        # Same side check for previous bar
        if side == "bearish" and hist_arr[j - 1] <= 0:
            break
        if side == "bullish" and hist_arr[j - 1] >= 0:
            break
        if curr_mag < prev_mag:
            count += 1
            j -= 1
        else:
            break
    return count


# ---------------------------------------------------------------------------
# Main scan function
# ---------------------------------------------------------------------------

def scan(df: pd.DataFrame, ticker: str) -> list[dict]:
    """
    Scan df for Strategy B — MACD Histogram Divergence signals (both directions).

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV data with DatetimeIndex and columns:
        open, high, low, close, volume, subperiod
    ticker : str
        Ticker symbol (for output tagging)

    Returns
    -------
    list of dict, one per signal
    """
    df = df.copy()
    df.sort_index(inplace=True)

    close = df["close"]
    high  = df["high"]
    low   = df["low"]

    # --- Compute indicators ---
    macd_line, signal_line, histogram = _compute_macd(close)
    rsi       = _compute_rsi(close, period=RSI_PERIOD)
    atr       = _compute_atr(high, low, close, period=ATR_PERIOD)

    # Convert to numpy arrays for indexed access
    close_arr  = close.values.astype(float)
    high_arr   = high.values.astype(float)
    low_arr    = low.values.astype(float)
    macd_arr   = macd_line.values.astype(float)
    signal_arr = signal_line.values.astype(float)
    hist_arr   = histogram.values.astype(float)
    rsi_arr    = rsi.values.astype(float)
    atr_arr    = atr.values.astype(float)
    dates      = df.index
    subperiod_arr = (
        df["subperiod"].values if "subperiod" in df.columns
        else np.full(len(df), "unknown")
    )

    signals = []

    # Minimum start index: need enough history for all lookbacks
    min_start = max(
        MACD_SLOW + MACD_SIGNAL,
        ATR_PERIOD,
        RSI_PERIOD,
        PRIOR_SWING_RANGE[1] + MATURITY_BARS + 5,
        TARGET_LOOKBACK + 5,
    )

    for i in range(min_start, len(df)):

        # Skip if any key indicator is NaN
        if (np.isnan(macd_arr[i])   or np.isnan(signal_arr[i]) or
                np.isnan(hist_arr[i])   or np.isnan(rsi_arr[i])    or
                np.isnan(atr_arr[i])    or np.isnan(macd_arr[i - 1])):
            continue

        # We'll check both directions in a loop to avoid duplicating logic
        for direction in ("bearish", "long_direction"):  # processed below
            pass

        # ===================================================================
        # BEARISH SIGNAL (short trade — divergence in uptrend)
        # ===================================================================
        bearish = _check_signal(
            i, close_arr, high_arr, low_arr,
            macd_arr, signal_arr, hist_arr, rsi_arr, atr_arr,
            direction="bearish",
        )
        if bearish is not None:
            entry_price, stop_price, target_price, conf_level, macd_bars, extra_b = bearish
            rr = (entry_price - target_price) / (stop_price - entry_price)
            if rr >= MIN_RR and target_price < entry_price:
                ep, er, bh = _simulate_exit(
                    close_arr, i, entry_price, stop_price, target_price, "short"
                )
                # Realised R: for short, profit when price falls (ep < entry)
                realised_r = (entry_price - ep) / (stop_price - entry_price)
                signals.append({
                    "ticker":               ticker,
                    "date":                 dates[i],
                    "direction":            "short",
                    "entry_price":          round(entry_price,  4),
                    "stop_price":           round(stop_price,   4),
                    "target_price":         round(target_price, 4),
                    "exit_price":           round(ep,           4),
                    "exit_reason":          er,
                    "r_multiple":           round(realised_r,   4),
                    "bars_held":            bh,
                    "subperiod":            subperiod_arr[i],
                    "strategy_id":          STRATEGY_ID,
                    "confirmation_level":   conf_level,
                    "macd_bars_above_zero": macd_bars,
                    "signal_bar_index":     i,
                    "narrowing_bars":       extra_b["narrowing_bars"],
                    "rsi_at_signal":        extra_b["rsi_at_signal"],
                    "prior_swing_bar_offset": extra_b["prior_swing_bar_offset"],
                    "dollar_volume_60d": float(np.mean(close_arr[max(0,i-DV_LOOKBACK):i+1] * df["volume"].values.astype(float)[max(0,i-DV_LOOKBACK):i+1])) if "volume" in df.columns else 0,
                })

        # ===================================================================
        # BULLISH SIGNAL (long trade — divergence in downtrend)
        # ===================================================================
        bullish = _check_signal(
            i, close_arr, high_arr, low_arr,
            macd_arr, signal_arr, hist_arr, rsi_arr, atr_arr,
            direction="bullish",
        )
        if bullish is not None:
            entry_price, stop_price, target_price, conf_level, macd_bars, extra_l = bullish
            rr = (target_price - entry_price) / (entry_price - stop_price)
            if rr >= MIN_RR and target_price > entry_price:
                ep, er, bh = _simulate_exit(
                    close_arr, i, entry_price, stop_price, target_price, "long"
                )
                # Realised R: for long, profit when price rises (ep > entry)
                realised_r = (ep - entry_price) / (entry_price - stop_price)
                signals.append({
                    "ticker":               ticker,
                    "date":                 dates[i],
                    "direction":            "long",
                    "entry_price":          round(entry_price,  4),
                    "stop_price":           round(stop_price,   4),
                    "target_price":         round(target_price, 4),
                    "exit_price":           round(ep,           4),
                    "exit_reason":          er,
                    "r_multiple":           round(realised_r,   4),
                    "bars_held":            bh,
                    "subperiod":            subperiod_arr[i],
                    "strategy_id":          STRATEGY_ID,
                    "confirmation_level":   conf_level,
                    "macd_bars_above_zero": macd_bars,
                    "signal_bar_index":     i,
                    "narrowing_bars":       extra_l["narrowing_bars"],
                    "rsi_at_signal":        extra_l["rsi_at_signal"],
                    "prior_swing_bar_offset": extra_l["prior_swing_bar_offset"],
                    "dollar_volume_60d": float(np.mean(close_arr[max(0,i-DV_LOOKBACK):i+1] * df["volume"].values.astype(float)[max(0,i-DV_LOOKBACK):i+1])) if "volume" in df.columns else 0,
                })

    return signals


# ---------------------------------------------------------------------------
# _check_signal: encapsulates all rule checks for one direction at bar i
# ---------------------------------------------------------------------------

def _check_signal(
    i: int,
    close_arr: np.ndarray,
    high_arr:  np.ndarray,
    low_arr:   np.ndarray,
    macd_arr:  np.ndarray,
    signal_arr: np.ndarray,
    hist_arr:  np.ndarray,
    rsi_arr:   np.ndarray,
    atr_arr:   np.ndarray,
    direction: str,          # 'bearish' or 'bullish'
) -> tuple | None:
    """
    Run all Strategy B checks for one bar and direction.
    Returns (entry_price, stop_price, target_price, conf_level, macd_bars)
    or None if any rule fails.
    """

    # -------------------------------------------------------------------
    # Maturity gate: MACD line must have spent >= MATURITY_BARS consecutive
    # bars on the correct side of zero BEFORE the current bar.
    # bearish: MACD above zero; bullish: MACD below zero
    # -------------------------------------------------------------------
    if direction == "bearish":
        macd_bars = _count_consecutive_above_zero(macd_arr, i - 1)
    else:
        macd_bars = _count_consecutive_below_zero(macd_arr, i - 1)

    if macd_bars < MATURITY_BARS:
        return None

    # -------------------------------------------------------------------
    # Stage 1: Histogram is narrowing AND price has made a new extreme
    # recently (within SWING_LOOKBACK bars). These don't need to be
    # on the exact same bar — divergence forms over several bars.
    # bearish: price made new 10-bar HIGH in last SWING_LOOKBACK bars,
    #          and histogram has been narrowing for NARROWING_BARS bars
    # bullish: mirror
    # -------------------------------------------------------------------
    if direction == "bearish":
        # Price at new high OR made new high within last SWING_LOOKBACK bars
        window_prices = high_arr[max(0, i - SWING_LOOKBACK): i + 1]
        is_near_extreme = high_arr[i] >= np.max(window_prices) * 0.99  # within 1% of recent high
        narrowing_count = _histogram_narrowing_count(hist_arr, i, "bearish")
    else:
        window_prices = low_arr[max(0, i - SWING_LOOKBACK): i + 1]
        is_near_extreme = low_arr[i] <= np.min(window_prices) * 1.01   # within 1% of recent low
        narrowing_count = _histogram_narrowing_count(hist_arr, i, "bullish")
    if not is_near_extreme:
        return None
    if narrowing_count < NARROWING_BARS:
        return None

    # -------------------------------------------------------------------
    # Stage 2: MACD line makes a lower high (bearish) / higher low (bullish)
    # vs. its reading 10-20 bars ago (at the prior price swing extreme).
    # We look for the bar of the prior swing extreme in [i-20 .. i-10],
    # then compare MACD values.
    # -------------------------------------------------------------------
    prior_start = i - PRIOR_SWING_RANGE[1]
    prior_end   = i - PRIOR_SWING_RANGE[0]
    if prior_start < 0:
        return None

    if direction == "bearish":
        # Find bar of prior price high in the range
        prior_window_prices = high_arr[prior_start: prior_end + 1]
        relative_idx = int(np.argmax(prior_window_prices))
        prior_swing_bar = prior_start + relative_idx
        # MACD should make a lower high: macd[i] < macd[prior_swing_bar]
        if macd_arr[i] >= macd_arr[prior_swing_bar]:
            return None
    else:
        # Find bar of prior price low in the range
        prior_window_prices = low_arr[prior_start: prior_end + 1]
        relative_idx = int(np.argmin(prior_window_prices))
        prior_swing_bar = prior_start + relative_idx
        # MACD should make a higher low: macd[i] > macd[prior_swing_bar]
        if macd_arr[i] <= macd_arr[prior_swing_bar]:
            return None

    # -------------------------------------------------------------------
    # Entry trigger: MACD line crosses the signal line
    # Allow trigger on current bar OR within next 2 bars (divergence
    # confirmation and crossover rarely land on same bar — crossover
    # typically follows 1-2 bars after divergence peak forms).
    # bearish: macd crosses BELOW signal
    # bullish: macd crosses ABOVE signal
    # -------------------------------------------------------------------
    crossover_bar = None
    for offset in range(0, 3):
        j = i + offset
        if j <= 0 or j >= len(macd_arr):
            break
        if direction == "bearish":
            if macd_arr[j] < signal_arr[j] and macd_arr[j - 1] >= signal_arr[j - 1]:
                crossover_bar = j
                break
        else:
            if macd_arr[j] > signal_arr[j] and macd_arr[j - 1] <= signal_arr[j - 1]:
                crossover_bar = j
                break

    if crossover_bar is None:
        return None

    # -------------------------------------------------------------------
    # Confirmation level: Level 2 if RSI >= 70 (bearish) or RSI <= 30 (bullish)
    # -------------------------------------------------------------------
    if direction == "bearish":
        conf_level = "Level 2" if rsi_arr[i] >= 70 else "Level 1"
    else:
        conf_level = "Level 2" if rsi_arr[i] <= 30 else "Level 1"

    # Extra fields surfaced for Discord alert / chart context (US-064).
    # narrowing_count and prior_swing_bar were computed above for the gate
    # checks; recompute the small ones here since they're cheap and this
    # keeps _check_signal's control flow unchanged above.
    if direction == "bearish":
        narrowing_count = _histogram_narrowing_count(hist_arr, i, "bearish")
    else:
        narrowing_count = _histogram_narrowing_count(hist_arr, i, "bullish")

    extra = {
        "narrowing_bars": narrowing_count,
        "rsi_at_signal": round(float(rsi_arr[i]), 1),
        "prior_swing_bar_offset": i - prior_swing_bar,
    }

    return crossover_bar, conf_level, macd_bars, extra


# ---------------------------------------------------------------------------
# __main__ — quick smoke test on SPY
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    data_path = Path.home() / ".hermes" / "market_data" / "SPY.parquet"
    if not data_path.exists():
        print(f"[ERROR] Data file not found: {data_path}")
        sys.exit(1)

    print(f"Loading data from {data_path} ...")
    df = pd.read_parquet(data_path)

    # Normalise column names to lowercase
    df.columns = [c.lower() for c in df.columns]

    # Ensure DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # Add subperiod column if missing
    if "subperiod" not in df.columns:
        df["subperiod"] = df.index.to_period("Q").astype(str)

    df.sort_index(inplace=True)
    print(f"Loaded {len(df)} rows  ({df.index[0]} → {df.index[-1]})")

    results = scan(df, ticker="SPY")
    print(f"\nStrategy B signals found: {len(results)}")

    long_sigs  = [s for s in results if s["direction"] == "long"]
    short_sigs = [s for s in results if s["direction"] == "short"]
    print(f"  Long  (bullish): {len(long_sigs)}")
    print(f"  Short (bearish): {len(short_sigs)}")

    if results:
        print("\nFirst 3 signals:")
        for sig in results[:3]:
            print("-" * 60)
            for k, v in sig.items():
                print(f"  {k:<26}: {v}")
    else:
        print("No signals detected.")
