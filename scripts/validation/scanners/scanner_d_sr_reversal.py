"""
scanner_d_sr_reversal.py
Strategy D — Support/Resistance Role-Reversal

Concept:
  Old resistance (price was rejected there before) becomes new support.
  After price pulls back to that level and then closes back above it,
  we enter long expecting continuation toward the next resistance above.

Entry logic:
  1. Identify prior resistance zone:
       resistance_level = max(high[i-60 : i-20])
       (Look 60 bars back but exclude the most recent 20 to avoid noise.)

  2. Pull-back to that level:
       abs(close[i] - resistance_level) / resistance_level <= 0.01
       (Today's close is within 1 % of the resistance level.)

  3. Breakout / re-confirmation trigger:
       close[i]   > resistance_level          — today closes back above it
       close[i-1] <= resistance_level * 1.01  — yesterday was at or below it
       (Two-bar sequence: touch then reclaim.)

  4. Stop:
       stop = resistance_level - 1.0 * ATR(14)
       (Give the level one ATR of breathing room below it.)

  5. Target:
       Next resistance above = highest high in the prior 100 bars that sits
       strictly above resistance_level.
       If none found → skip this trade.

  6. R:R filter: skip if (target - entry) / (entry - stop) < 3.0

Exit simulation (forward scan, up to 8 bars):
  - 'target' : close >= target_price
  - 'stop'   : close <= stop_price
  - 'time'   : 8-bar time stop

Output fields per signal:
  ticker, date, entry_price, stop_price, target_price,
  exit_price, exit_reason, r_multiple, bars_held,
  subperiod, strategy_id, level_age_bars, touch_depth_pct
"""

import pandas as pd
import numpy as np
from pathlib import Path

STRATEGY_ID       = "D_sr_reversal"
RESIST_LOOKBACK   = 60   # max bars back to search for prior resistance
RESIST_RECENT_EX  = 20   # exclude last N bars from resistance search (keep it "prior")
ATR_PERIOD        = 14   # period for ATR calculation
ATR_STOP_MULT     = 1.0  # ATR multiplier for stop distance
TOUCH_THRESHOLD   = 0.01 # ±1 % band around resistance counts as "touching"
MIN_RR            = 3.0  # minimum reward-to-risk ratio
MAX_HOLD          = 8    # bars for time stop
TARGET_LOOKBACK   = 100  # bars to scan for "next resistance above"


# --------------------------------------------------------------------------- #
# Helper: ATR (Wilder / simple average of True Range)                         #
# --------------------------------------------------------------------------- #
def _atr(df: pd.DataFrame, period: int, end_idx: int) -> float:
    """
    Compute a simple-average ATR over the last `period` bars ending at end_idx.
    Returns 0.0 if there is insufficient data.
    """
    start = end_idx - period
    if start < 1:
        return 0.0  # not enough bars

    highs  = df["high"].iloc[start : end_idx + 1].values
    lows   = df["low"].iloc[start : end_idx + 1].values
    closes = df["close"].iloc[start : end_idx + 1].values

    # True Range for each bar (requires the previous close)
    prev_closes = closes[:-1]
    tr = np.maximum(
        highs[1:]  - lows[1:],              # high - low
        np.maximum(
            np.abs(highs[1:]  - prev_closes),  # |high - prev_close|
            np.abs(lows[1:]   - prev_closes),  # |low  - prev_close|
        ),
    )
    if len(tr) == 0:
        return 0.0
    return float(tr[-period:].mean())


# --------------------------------------------------------------------------- #
# Helper: sub-period label                                                    #
# --------------------------------------------------------------------------- #
def _subperiod(date: str) -> str:
    """Return a quarterly sub-period string from an ISO date string."""
    ts = pd.Timestamp(date)
    return f"{ts.year}-Q{ts.quarter}"


# --------------------------------------------------------------------------- #
# Helper: simulate exit                                                        #
# --------------------------------------------------------------------------- #
def _simulate_exit(
    df: pd.DataFrame,
    entry_idx: int,
    entry_price: float,
    stop_price: float,
    target_price: float,
) -> dict:
    """
    Walk forward up to MAX_HOLD bars from entry.
    Returns exit_price, exit_reason, bars_held, r_multiple.
    """
    risk = entry_price - stop_price  # > 0 guaranteed by caller
    n    = len(df)

    for offset in range(1, MAX_HOLD + 1):
        bar_idx = entry_idx + offset
        if bar_idx >= n:
            # Ran out of data — close out at last available close
            last_close = df["close"].iloc[min(bar_idx - 1, n - 1)]
            return dict(
                exit_price  = round(float(last_close), 4),
                exit_reason = "time",
                bars_held   = offset,
                r_multiple  = round((float(last_close) - entry_price) / risk, 3),
            )

        close = float(df["close"].iloc[bar_idx])

        # Stop check first (protect capital)
        if close <= stop_price:
            return dict(
                exit_price  = round(close, 4),
                exit_reason = "stop",
                bars_held   = offset,
                r_multiple  = round((close - entry_price) / risk, 3),
            )

        # Target check
        if close >= target_price:
            return dict(
                exit_price  = round(close, 4),
                exit_reason = "target",
                bars_held   = offset,
                r_multiple  = round((close - entry_price) / risk, 3),
            )

    # Time stop: exhausted MAX_HOLD bars without hitting either level
    last_close = float(df["close"].iloc[entry_idx + MAX_HOLD])
    return dict(
        exit_price  = round(last_close, 4),
        exit_reason = "time",
        bars_held   = MAX_HOLD,
        r_multiple  = round((last_close - entry_price) / risk, 3),
    )


# --------------------------------------------------------------------------- #
# Main scanner                                                                 #
# --------------------------------------------------------------------------- #
def scan(df: pd.DataFrame, ticker: str) -> list[dict]:
    """
    Scan a price DataFrame for Strategy D signals.

    Parameters
    ----------
    df     : DataFrame with columns [open, high, low, close, volume]
             sorted chronologically (oldest first), DatetimeIndex.
    ticker : Ticker symbol string (for output labelling).

    Returns
    -------
    List of signal dicts, one per triggered bar.
    """
    df = df.copy()

    # --- Normalise column names ---
    df.columns = df.columns.str.lower()
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(df.columns):
        raise ValueError(f"DataFrame missing columns: {required - set(df.columns)}")

    signals: list[dict] = []

    # Minimum history needed:
    #   RESIST_LOOKBACK bars + ATR_PERIOD bars + 1 prior-close for trigger
    min_history = max(RESIST_LOOKBACK, TARGET_LOOKBACK) + ATR_PERIOD + 2

    for i in range(min_history, len(df)):

        # -------------------------------------------------------------- #
        # 1. Identify prior resistance level                               #
        #    Window: bars [i-60, i-20)  (60 bars back, skip recent 20)    #
        # -------------------------------------------------------------- #
        resist_start = i - RESIST_LOOKBACK   # inclusive
        resist_end   = i - RESIST_RECENT_EX  # exclusive (not too recent)

        if resist_start < 0:
            continue  # not enough history

        prior_highs      = df["high"].iloc[resist_start : resist_end]
        resistance_level = float(prior_highs.max())

        # Rough age: midpoint of the resistance window
        level_age_bars = RESIST_RECENT_EX + (RESIST_LOOKBACK - RESIST_RECENT_EX) // 2

        # -------------------------------------------------------------- #
        # 2. Today's and yesterday's close                                #
        # -------------------------------------------------------------- #
        close_today = float(df["close"].iloc[i])
        close_prev  = float(df["close"].iloc[i - 1])

        # -------------------------------------------------------------- #
        # 3a. Pull-back-to-level check: today is within ±1 % of level    #
        # -------------------------------------------------------------- #
        touch_depth_pct = abs(close_today - resistance_level) / resistance_level
        if touch_depth_pct > TOUCH_THRESHOLD:
            continue

        # -------------------------------------------------------------- #
        # 3b. Trigger: today closes ABOVE level; yesterday was at/below   #
        # -------------------------------------------------------------- #
        if not (close_today > resistance_level):
            continue
        if not (close_prev <= resistance_level * 1.01):
            continue

        # -------------------------------------------------------------- #
        # 4. Stop = resistance_level - 1 × ATR(14)                        #
        # -------------------------------------------------------------- #
        atr = _atr(df, ATR_PERIOD, i)
        if atr <= 0.0:
            continue  # skip bars with zero / undefined ATR

        entry_price = close_today
        stop_price  = resistance_level - ATR_STOP_MULT * atr

        # Guard: stop must be below entry
        if stop_price >= entry_price:
            continue

        # -------------------------------------------------------------- #
        # 5. Target = highest high in prior 100 bars that is above level  #
        # -------------------------------------------------------------- #
        target_window_start = max(0, i - TARGET_LOOKBACK)
        target_window_end   = i  # up to but not including today

        candidate_highs = df["high"].iloc[target_window_start : target_window_end]
        # Keep only highs that are strictly above the resistance level
        above_level = candidate_highs[candidate_highs > resistance_level]

        if above_level.empty:
            continue  # no identifiable target above — skip trade

        target_price = float(above_level.max())

        # Target must be above entry price to be meaningful
        if target_price <= entry_price:
            continue

        # -------------------------------------------------------------- #
        # 6. R:R filter                                                   #
        # -------------------------------------------------------------- #
        risk   = entry_price - stop_price
        reward = target_price - entry_price
        rr     = reward / risk
        if rr < MIN_RR:
            continue

        # -------------------------------------------------------------- #
        # 7. Simulate exit                                                 #
        # -------------------------------------------------------------- #
        exit_info = _simulate_exit(df, i, entry_price, stop_price, target_price)

        # -------------------------------------------------------------- #
        # 8. Build signal record                                           #
        # -------------------------------------------------------------- #
        raw_date = str(df.index[i])          # convert index element to str
        ts       = pd.Timestamp(raw_date)    # safe Timestamp construction

        signals.append(dict(
            ticker          = ticker,
            date            = ts.date(),
            entry_price     = round(entry_price, 4),
            stop_price      = round(stop_price, 4),
            target_price    = round(target_price, 4),
            subperiod       = f"{ts.year}-Q{ts.quarter}",
            strategy_id     = STRATEGY_ID,
            level_age_bars  = level_age_bars,
            touch_depth_pct = round(touch_depth_pct * 100, 4),  # store as %
            **exit_info,
        ))

    return signals


# --------------------------------------------------------------------------- #
# __main__ : quick smoke test against cached SPY data                         #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import sys

    cache_path = Path.home() / ".hermes" / "market_data" / "SPY.parquet"
    if not cache_path.exists():
        print(f"[ERROR] Cache file not found: {cache_path}", file=sys.stderr)
        sys.exit(1)

    spy_df = pd.read_parquet(cache_path)
    print(f"Loaded SPY: {len(spy_df)} bars  ({spy_df.index[0]} → {spy_df.index[-1]})")

    results = scan(spy_df, "SPY")
    print(f"\nStrategy D signals found: {len(results)}")

    if results:
        print("\nFirst 3 signals:")
        for sig in results[:3]:
            for k, v in sig.items():
                print(f"  {k:25s}: {v}")
            print()
