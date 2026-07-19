"""
scanner_c_breakout_volume.py
Strategy C — Breakout + Volume Confirmation

Entry logic:
  - Price closes above the highest high of the prior 20 bars (not including today)
  - Volume on the breakout bar is at least 1.5× the 20-bar average volume
  - Entry price  = close of breakout bar
  - Stop price   = low of breakout bar
  - Target price = entry + (entry - prior_base_low)
                   where prior_base_low = min(low[-20:-1])

Filters:
  - Skip if R:R < 3.0
  - Skip if stop == entry (zero-range / doji bar)

Exit simulation (forward scan up to 8 bars):
  - 'target' : close >= target_price
  - 'stop'   : close <= stop_price
  - 'time'   : neither hit within 8 bars

Output fields per signal:
  ticker, date, entry_price, stop_price, target_price,
  exit_price, exit_reason, r_multiple, bars_held,
  subperiod, strategy_id, volume_ratio, breakout_bar_range
"""

import pandas as pd
import numpy as np
from pathlib import Path

STRATEGY_ID = "C_breakout_volume"
LOOKBACK     = 20          # bars for breakout / volume baseline
VOLUME_MULT  = 1.5         # volume confirmation multiplier
MIN_RR       = 3.0         # minimum reward-to-risk ratio
MAX_HOLD     = 8           # maximum bars to hold (time stop)
MIN_BARS     = LOOKBACK + 2  # minimum rows needed before we can scan


def _subperiod(date: "pd.Timestamp | pd.NaTType") -> str:  # type: ignore[name-defined]
    """Assign a calendar sub-period label (quarter) to a date."""
    ts = pd.Timestamp(str(date))   # always a concrete Timestamp after str round-trip
    return f"{ts.year}-Q{ts.quarter}"


def _simulate_exit(
    df: pd.DataFrame,
    entry_idx: int,
    entry_price: float,
    stop_price: float,
    target_price: float,
) -> dict:
    """
    Walk forward from the bar *after* entry for up to MAX_HOLD bars.
    Returns a dict with exit_price, exit_reason, bars_held, r_multiple.
    """
    risk = entry_price - stop_price  # > 0 guaranteed by caller
    n    = len(df)

    for offset in range(1, MAX_HOLD + 1):
        bar_idx = entry_idx + offset
        if bar_idx >= n:
            # Ran out of data — treat as time stop at last known close
            last_close = df["close"].iloc[bar_idx - 1] if bar_idx > 0 else entry_price
            r_mult = (last_close - entry_price) / risk
            return dict(
                exit_price  = round(last_close, 4),
                exit_reason = "time",
                bars_held   = offset,
                r_multiple  = round(r_mult, 3),
            )

        close = df["close"].iloc[bar_idx]

        # Check stop first (protects capital)
        if close <= stop_price:
            r_mult = (close - entry_price) / risk
            return dict(
                exit_price  = round(close, 4),
                exit_reason = "stop",
                bars_held   = offset,
                r_multiple  = round(r_mult, 3),
            )

        # Check target
        if close >= target_price:
            r_mult = (close - entry_price) / risk
            return dict(
                exit_price  = round(close, 4),
                exit_reason = "target",
                bars_held   = offset,
                r_multiple  = round(r_mult, 3),
            )

    # Time stop: neither target nor stop hit within MAX_HOLD bars
    last_close = df["close"].iloc[entry_idx + MAX_HOLD]
    r_mult = (last_close - entry_price) / risk
    return dict(
        exit_price  = round(last_close, 4),
        exit_reason = "time",
        bars_held   = MAX_HOLD,
        r_multiple  = round(r_mult, 3),
    )


def scan(df: pd.DataFrame, ticker: str) -> list[dict]:
    """
    Scan a price DataFrame for Strategy C signals.

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

    # --- Normalise column names to lowercase ---
    df.columns = df.columns.str.lower()
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(df.columns):
        raise ValueError(f"DataFrame missing columns: {required - set(df.columns)}")

    signals: list[dict] = []

    # We need at least LOOKBACK bars of history before index i
    for i in range(LOOKBACK, len(df)):

        # ------------------------------------------------------------------ #
        # 1. Define the lookback window (prior 20 bars, NOT including today)  #
        # ------------------------------------------------------------------ #
        window_high   = df["high"].iloc[i - LOOKBACK : i]   # bars i-20 .. i-1
        window_low    = df["low"].iloc[i - LOOKBACK : i]
        window_volume = df["volume"].iloc[i - LOOKBACK : i]

        prior_resistance = window_high.max()   # highest high in prior 20 bars
        prior_base_low   = window_low.min()    # lowest low in prior 20 bars

        today_close  = df["close"].iloc[i]
        today_volume = df["volume"].iloc[i]
        today_low    = df["low"].iloc[i]

        # ------------------------------------------------------------------ #
        # 2. Breakout condition: today closes ABOVE the prior 20-bar high     #
        # ------------------------------------------------------------------ #
        if today_close <= prior_resistance:
            continue

        # ------------------------------------------------------------------ #
        # 3. Volume confirmation: today's vol > 1.5× 20-bar average           #
        # ------------------------------------------------------------------ #
        avg_volume   = window_volume.mean()
        volume_ratio = today_volume / avg_volume if avg_volume > 0 else 0.0
        if volume_ratio < VOLUME_MULT:
            continue

        # ------------------------------------------------------------------ #
        # 4. Calculate entry, stop, target                                    #
        # ------------------------------------------------------------------ #
        entry_price  = today_close
        stop_price   = today_low

        # Skip zero-range bar (stop == entry would produce infinite R:R)
        if stop_price >= entry_price:
            continue

        # Target = mirror the base depth above entry
        base_depth   = entry_price - prior_base_low
        target_price = entry_price + base_depth

        # ------------------------------------------------------------------ #
        # 5. R:R filter                                                       #
        # ------------------------------------------------------------------ #
        risk   = entry_price - stop_price        # always > 0 after above check
        reward = target_price - entry_price      # = base_depth
        rr     = reward / risk
        if rr < MIN_RR:
            continue

        # ------------------------------------------------------------------ #
        # 6. Simulate exit (forward scan)                                     #
        # ------------------------------------------------------------------ #
        exit_info = _simulate_exit(df, i, entry_price, stop_price, target_price)

        # ------------------------------------------------------------------ #
        # 7. Build signal record                                               #
        # ------------------------------------------------------------------ #
        raw_date  = df.index[i]
        # Cast via str to satisfy static type checkers; pd.Timestamp accepts
        # ISO strings so this is safe at runtime for any DatetimeIndex.
        ts        = pd.Timestamp(str(raw_date))
        date_val  = ts.date()
        signals.append(dict(
            ticker             = ticker,
            date               = date_val,
            entry_price        = round(entry_price, 4),
            stop_price         = round(stop_price, 4),
            target_price       = round(target_price, 4),
            subperiod          = _subperiod(ts),
            strategy_id        = STRATEGY_ID,
            volume_ratio       = round(volume_ratio, 4),
            breakout_bar_range = round(entry_price - today_low, 4),
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
    print(f"\nStrategy C signals found: {len(results)}")

    if results:
        print("\nFirst 3 signals:")
        for sig in results[:3]:
            for k, v in sig.items():
                print(f"  {k:25s}: {v}")
            print()
