"""
scanner_a_ma_pullback.py
========================
HermesForge Phase 1A — Strategy A: MA Pullback with Fibonacci Entry

Signal Rules:
  1. 50-day MA is rising (slope > 0): MA50[i] > MA50[i-5]
  2. Weekly trend proxy: close > 200-day MA
  3. Prior advance: highest high and lowest low over prior 40 bars,
     advance (high - low) / low >= 8%
  4. Fibonacci retracement: current price within 38%–62% retracement
     of that advance (38.2% and 61.8% levels)
  5. Entry trigger: RSI(14) crosses above 40 (rsi[i] > 40 AND rsi[i-1] <= 40)

Exit simulation (forward-scan from entry bar, max 8 bars):
  - 'target' if close >= target_price
  - 'stop'   if close <= stop_price
  - 'time'   if neither hit within 8 bars

Dependencies: pandas, numpy only.
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "A_MA_PULLBACK"
LOOKBACK_BARS = 40          # bars to look back for prior advance
RSI_PERIOD = 14
MA_FAST = 50
MA_SLOW = 200
MA_SLOPE_LOOKBACK = 5       # bars to measure MA50 slope
FIB_LOW = 0.382             # 38.2% retracement
FIB_MID = 0.500             # 50.0% retracement
FIB_HIGH = 0.618            # 61.8% retracement (also stop level)
MIN_ADVANCE_PCT = 0.08      # 8% minimum prior advance
MIN_RR = 3.0                # minimum reward-to-risk ratio
MAX_BARS_HELD = 8           # time-stop


# ---------------------------------------------------------------------------
# Indicator helpers
# ---------------------------------------------------------------------------

def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder-smoothed RSI using EWM (alpha = 1/period)."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    # Wilder smoothing = EWM with alpha=1/period, adjust=False
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _compute_mas(close: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Return (MA50, MA200) as simple rolling means."""
    ma50 = close.rolling(window=MA_FAST, min_periods=MA_FAST).mean()
    ma200 = close.rolling(window=MA_SLOW, min_periods=MA_SLOW).mean()
    return ma50, ma200


# ---------------------------------------------------------------------------
# Exit simulation helper
# ---------------------------------------------------------------------------

def _simulate_exit(
    df: pd.DataFrame,
    entry_idx: int,
    entry_price: float,
    stop_price: float,
    target_price: float,
) -> tuple[float, str, int]:
    """
    Scan forward from the bar *after* entry_idx for up to MAX_BARS_HELD bars.
    Returns (exit_price, exit_reason, bars_held).
    """
    closes = df["close"].values
    n = len(closes)

    for offset in range(1, MAX_BARS_HELD + 1):
        idx = entry_idx + offset
        if idx >= n:
            # End of data — treat as time stop at last available close
            last_idx = min(entry_idx + offset - 1, n - 1)
            return closes[last_idx], "time", offset
        c = closes[idx]
        # Check target first (optimistic), then stop
        if c >= target_price:
            return c, "target", offset
        if c <= stop_price:
            return c, "stop", offset

    # Time stop: exit at close of bar MAX_BARS_HELD after entry
    exit_idx = min(entry_idx + MAX_BARS_HELD, n - 1)
    return closes[exit_idx], "time", MAX_BARS_HELD


# ---------------------------------------------------------------------------
# Fibonacci zone label
# ---------------------------------------------------------------------------

def _fib_zone(price: float, low: float, high: float) -> str:
    """
    Returns label based on where within the 38%–62% retracement zone
    the current price sits.
      38pct   : within 1% of the 38.2% level
      50pct   : within 1% of the 50.0% level
      between : anywhere else inside the 38%–62% band
    """
    advance = high - low
    level_38 = high - FIB_LOW * advance
    level_50 = high - FIB_MID * advance
    tol = 0.01 * advance  # 1% of the advance as tolerance band

    if abs(price - level_38) <= tol:
        return "38pct"
    if abs(price - level_50) <= tol:
        return "50pct"
    return "between"


# ---------------------------------------------------------------------------
# Main scan function
# ---------------------------------------------------------------------------

def scan(df: pd.DataFrame, ticker: str) -> list[dict]:
    """
    Scan df for Strategy A — MA Pullback / Fibonacci Entry signals.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV data with DatetimeIndex and columns:
        open, high, low, close, volume, subperiod
    ticker : str
        Ticker symbol (used for output tagging only)

    Returns
    -------
    list of dict, one per signal detected
    """
    df = df.copy()
    df.sort_index(inplace=True)

    close = df["close"]
    high  = df["high"]

    # --- Compute indicators ---
    ma50, ma200 = _compute_mas(close)
    rsi = _compute_rsi(close, period=RSI_PERIOD)

    # Convert to numpy for fast indexed access
    close_arr = close.values
    high_arr  = high.values
    low_arr   = df["low"].values
    ma50_arr  = ma50.values
    ma200_arr = ma200.values
    rsi_arr   = rsi.values
    dates     = df.index
    subperiod_arr = df["subperiod"].values if "subperiod" in df.columns else np.full(len(df), "unknown")

    signals = []

    # We need enough history: max(MA_SLOW, LOOKBACK_BARS) + a few extra bars
    min_start = max(MA_SLOW, LOOKBACK_BARS) + MA_SLOPE_LOOKBACK + 1

    for i in range(min_start, len(df)):

        # ---------------------------------------------------------------
        # Rule 1: MA50 is rising — MA50[i] > MA50[i - slope_lookback]
        # ---------------------------------------------------------------
        if np.isnan(ma50_arr[i]) or np.isnan(ma50_arr[i - MA_SLOPE_LOOKBACK]):
            continue
        if ma50_arr[i] <= ma50_arr[i - MA_SLOPE_LOOKBACK]:
            continue

        # ---------------------------------------------------------------
        # Rule 2: Weekly trend proxy — close > MA200
        # ---------------------------------------------------------------
        if np.isnan(ma200_arr[i]):
            continue
        ma200_above = bool(close_arr[i] > ma200_arr[i])
        if not ma200_above:
            continue  # Only take signals above MA200

        # ---------------------------------------------------------------
        # Rule 3: Prior advance — highest high & lowest low over 40 bars
        #         Advance must be >= 8%
        # ---------------------------------------------------------------
        window_high_arr = high_arr[i - LOOKBACK_BARS: i]
        window_low_arr  = low_arr[i - LOOKBACK_BARS: i]
        swing_high = float(np.max(window_high_arr))
        swing_low  = float(np.min(window_low_arr))

        advance_pct = (swing_high - swing_low) / swing_low
        if advance_pct < MIN_ADVANCE_PCT:
            continue

        # ---------------------------------------------------------------
        # Rule 4: Price within Fibonacci retracement zone (38%–62%)
        #         Retracement is measured from the swing move:
        #           fib_38 = swing_high - 0.382 * advance
        #           fib_62 = swing_high - 0.618 * advance
        #         Price must be BETWEEN fib_62 (lower) and fib_38 (upper)
        # ---------------------------------------------------------------
        advance = swing_high - swing_low
        fib_38  = swing_high - FIB_LOW  * advance   # upper boundary of zone
        fib_62  = swing_high - FIB_HIGH * advance   # lower boundary (also stop)

        price = close_arr[i]
        if not (fib_62 <= price <= fib_38):
            continue

        # ---------------------------------------------------------------
        # Rule 5: RSI(14) crosses above 40 from below
        #         rsi[i] > 40 AND rsi[i-1] <= 40
        # ---------------------------------------------------------------
        if np.isnan(rsi_arr[i]) or np.isnan(rsi_arr[i - 1]):
            continue
        if not (rsi_arr[i] > 40 and rsi_arr[i - 1] <= 40):
            continue

        # ---------------------------------------------------------------
        # Levels: stop = fib_62 level, target = swing_high
        # ---------------------------------------------------------------
        entry_price  = price
        stop_price   = fib_62
        target_price = swing_high

        risk   = entry_price - stop_price
        reward = target_price - entry_price

        if risk <= 0:
            continue  # degenerate case

        # Minimum risk filter: stop must be at least 0.5% of entry price away
        # Prevents degenerate trades where price is right at the 62% level
        if risk / entry_price < 0.005:
            continue

        r_multiple = reward / risk

        # ---------------------------------------------------------------
        # R:R filter
        # ---------------------------------------------------------------
        if r_multiple < MIN_RR:
            continue

        # ---------------------------------------------------------------
        # Tag fields
        # ---------------------------------------------------------------
        fib_zone = _fib_zone(entry_price, swing_low, swing_high)

        # ---------------------------------------------------------------
        # Exit simulation
        # ---------------------------------------------------------------
        exit_price, exit_reason, bars_held = _simulate_exit(
            df, i, entry_price, stop_price, target_price
        )

        # ---------------------------------------------------------------
        # Realised R-multiple based on actual exit price (not theoretical)
        # Positive = profit, negative = loss
        # ---------------------------------------------------------------
        realised_r = (exit_price - entry_price) / risk

        # ---------------------------------------------------------------
        # Build output record
        # ---------------------------------------------------------------
        signal = {
            "ticker":       ticker,
            "date":         dates[i],
            "entry_price":  round(entry_price,  4),
            "stop_price":   round(stop_price,   4),
            "target_price": round(target_price, 4),
            "exit_price":   round(exit_price,   4),
            "exit_reason":  exit_reason,
            "r_multiple":   round(realised_r,  4),
            "bars_held":    bars_held,
            "subperiod":    subperiod_arr[i],
            "strategy_id":  STRATEGY_ID,
            "fib_zone":     fib_zone,
            "ma200_above":  ma200_above,
        }
        signals.append(signal)

    return signals


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

    # Add subperiod column if missing (use year-quarter as proxy)
    if "subperiod" not in df.columns:
        df["subperiod"] = df.index.to_period("Q").astype(str)

    df.sort_index(inplace=True)
    print(f"Loaded {len(df)} rows  ({df.index[0].date()} → {df.index[-1].date()})")

    results = scan(df, ticker="SPY")
    print(f"\nStrategy A signals found: {len(results)}")

    if results:
        print("\nFirst 3 signals:")
        for sig in results[:3]:
            print("-" * 60)
            for k, v in sig.items():
                print(f"  {k:<18}: {v}")
    else:
        print("No signals detected.")
