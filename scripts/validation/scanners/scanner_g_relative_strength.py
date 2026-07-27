"""
scanner_g_relative_strength.py
Strategy G — Relative-Strength / Sector-Rotation Breakout

Entry logic (long-only):
  - Relative Strength (RS) line = ticker_close / spy_close, aligned on the
    dates common to both series (inner join).
  - RS_SMA20 = 20-period SMA of the RS line.
  - RS_ROC   = (RS[i] / RS[i-20] - 1)  -- 20-bar rate of change of the RS line.
  - LONG signal fires when ALL of:
      a) RS line crosses above RS_SMA20 today
         (yesterday RS < RS_SMA20, today RS >= RS_SMA20)
      b) RS_ROC > 0 (RS line has been rising over the past 20 bars)
      c) Ticker's own close is above its own 50-period SMA
  - Entry price  = close of signal bar
  - Stop price   = low of the most recent 10 bars (swing-low stop)
  - Target price = entry + 2.5 * (entry - stop)   (2.5:1 R:R)

Filters:
  - Skip if stop >= entry (zero/negative risk)
  - Skip if fewer than 50 bars of history (SMA50 warmup)
  - Skip if fewer than 40 aligned bars with SPY
    (20 for RS_SMA20 warmup + 20 for RS_ROC lookback)
  - Ticker == 'SPY' is skipped entirely (RS vs. self is meaningless)

Exit simulation (forward scan up to 10 bars, long-only):
  - 'target' : close >= target_price
  - 'stop'   : close <= stop_price
  - 'time'   : neither hit within 10 bars

Output fields per signal:
  ticker, date, entry_price, stop_price, target_price, direction,
  exit_price, exit_reason, bars_held, r_multiple, subperiod, strategy_id

The SPY benchmark series is loaded once from the local Hermes market-data
cache (~/.hermes/market_data/SPY.parquet) and memoised in a module-level
global so repeated calls to scan() across many tickers don't re-read the
file from disk each time.

Dependencies: pandas only.
"""

import pandas as pd
from pathlib import Path

STRATEGY_ID   = "STR-G-relative-strength-rotation"
RS_SMA_LEN    = 20     # SMA length applied to the RS line
RS_ROC_LEN    = 20     # lookback for RS rate-of-change
SMA50_LEN     = 50     # ticker's own trend filter
STOP_LOOKBACK = 10     # swing-low stop window
RR_MULT       = 2.5    # reward:risk multiple for target
MAX_HOLD      = 10     # maximum bars to hold (time stop)
MIN_BARS      = SMA50_LEN            # need SMA50 warmup
MIN_ALIGNED   = RS_SMA_LEN + RS_ROC_LEN  # need 40 aligned bars w/ SPY

_SPY_CACHE_PATH = Path.home() / ".hermes" / "market_data" / "SPY.parquet"

# Module-level lazy singleton -- loaded once, reused across all scan() calls.
_SPY_DF: "pd.DataFrame | None" = None


def _load_spy() -> pd.DataFrame:
    """Load & cache the SPY benchmark OHLCV DataFrame (lazy singleton)."""
    global _SPY_DF
    if _SPY_DF is None:
        if not _SPY_CACHE_PATH.exists():
            raise FileNotFoundError(f"SPY cache not found: {_SPY_CACHE_PATH}")
        spy = pd.read_parquet(_SPY_CACHE_PATH)
        spy.columns = spy.columns.str.lower()
        spy = spy.sort_index()
        _SPY_DF = spy
    return _SPY_DF


def _subperiod(date: "pd.Timestamp | pd.NaTType") -> str:  # type: ignore[name-defined]
    """Assign a calendar sub-period label (quarter) to a date."""
    ts = pd.Timestamp(str(date))
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
    Scan a price DataFrame for Strategy G (relative-strength / sector
    rotation breakout) signals.

    Parameters
    ----------
    df     : DataFrame with columns [open, high, low, close, volume]
             sorted chronologically (oldest first), DatetimeIndex.
    ticker : Ticker symbol string (for output labelling).

    Returns
    -------
    List of signal dicts, one per triggered bar.
    """
    # RS vs. self is meaningless -- skip the benchmark ticker entirely.
    if ticker == "SPY":
        return []

    df = df.copy()
    df.columns = df.columns.str.lower()
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(df.columns):
        raise ValueError(f"DataFrame missing columns: {required - set(df.columns)}")
    df = df.sort_index()

    if len(df) < MIN_BARS:
        return []

    spy_df = _load_spy()

    # --- Align ticker & SPY closes on the dates common to both (inner join) ---
    aligned = pd.DataFrame({
        "ticker_close": df["close"],
        "spy_close":    spy_df["close"],
    }).dropna()

    if len(aligned) < MIN_ALIGNED:
        return []

    # --- Relative-strength line & its indicators ---
    rs           = aligned["ticker_close"] / aligned["spy_close"]
    rs_sma20     = rs.rolling(RS_SMA_LEN).mean()
    rs_roc       = rs / rs.shift(RS_ROC_LEN) - 1.0

    # Ticker's own trend filter (computed on the full df, not just aligned dates)
    sma50 = df["close"].rolling(SMA50_LEN).mean()

    signals: list[dict] = []

    aligned_dates = aligned.index

    # Start once we have enough RS history (RS_SMA_LEN + RS_ROC_LEN warmup)
    for j in range(MIN_ALIGNED, len(aligned_dates)):
        date = aligned_dates[j]

        rs_today     = rs.iloc[j]
        rs_yesterday = rs.iloc[j - 1]
        sma_today    = rs_sma20.iloc[j]
        sma_yesterday = rs_sma20.iloc[j - 1]
        roc_today    = rs_roc.iloc[j]

        if pd.isna(sma_today) or pd.isna(sma_yesterday) or pd.isna(roc_today):
            continue

        # a) RS crosses above RS_SMA20 today
        crossed_up = (rs_yesterday < sma_yesterday) and (rs_today >= sma_today)
        if not crossed_up:
            continue

        # b) RS momentum positive
        if not (roc_today > 0):
            continue

        # Locate this date's position in the original (full) df
        if date not in df.index:
            continue
        i = df.index.get_loc(date)
        if isinstance(i, slice) or not isinstance(i, int):
            continue

        # c) Ticker's own price above its own SMA50
        sma50_today = sma50.iloc[i]
        if pd.isna(sma50_today):
            continue
        today_close = df["close"].iloc[i]
        if not (today_close > sma50_today):
            continue

        # Need at least STOP_LOOKBACK prior bars for the swing-low stop
        if i < STOP_LOOKBACK:
            continue

        entry_price = today_close
        stop_price  = df["low"].iloc[i - STOP_LOOKBACK:i].min()

        # Skip zero/negative risk
        if stop_price >= entry_price:
            continue

        risk         = entry_price - stop_price
        target_price = entry_price + RR_MULT * risk

        exit_info = _simulate_exit(df, i, entry_price, stop_price, target_price)

        ts       = pd.Timestamp(str(df.index[i]))
        date_val = ts.date()

        signals.append(dict(
            ticker       = ticker,
            date         = date_val,
            entry_price  = round(entry_price, 4),
            stop_price   = round(stop_price, 4),
            target_price = round(target_price, 4),
            direction    = "long",
            subperiod    = _subperiod(ts),
            strategy_id  = STRATEGY_ID,
            **exit_info,
        ))

    return signals


# --------------------------------------------------------------------------- #
# __main__ : quick smoke test against a cached non-SPY ticker                 #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import sys

    test_ticker = "AAPL"
    cache_path = Path.home() / ".hermes" / "market_data" / f"{test_ticker}.parquet"
    if not cache_path.exists():
        print(f"[ERROR] Cache file not found: {cache_path}", file=sys.stderr)
        sys.exit(1)

    test_df = pd.read_parquet(cache_path)
    test_df.columns = test_df.columns.str.lower()
    print(f"Loaded {test_ticker}: {len(test_df)} bars  ({test_df.index[0]} -> {test_df.index[-1]})")

    results = scan(test_df, test_ticker)
    print(f"\nStrategy G signals found: {len(results)}")

    # Also verify SPY-vs-self short-circuit returns [] without error
    spy_df_test = pd.read_parquet(_SPY_CACHE_PATH)
    spy_df_test.columns = spy_df_test.columns.str.lower()
    spy_results = scan(spy_df_test, "SPY")
    print(f"SPY self-scan signals (should be 0): {len(spy_results)}")

    if results:
        print("\nFirst 3 signals:")
        for sig in results[:3]:
            for k, v in sig.items():
                print(f"  {k:25s}: {v}")
            print()
