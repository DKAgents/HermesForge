"""
scanner_h_first_pullback_trend_swing.py
========================================
HermesForge Phase 1A — Strategy H: High-RR First-Pullback Trend Swing (Long/Short) v1.4

Source: 06-Strategies/Hypotheses/STR-20260726-first-pullback-trend-swing.md

Signal Rules (v1.4, swing-segmented leg definition):
  Regime (via SPY/VIX, loaded once and memoised):
    - Risk-on (longs only): SPY close > 50-SMA AND SPY close > 200-SMA AND VIX < 25
    - Risk-off (shorts only): SPY close < 50-SMA AND SPY close < 200-SMA
      (VIX > 25 while risk-off is a 50% size-reduction flag only, never an
       independent trigger -- tagged on the signal as `vix_size_reduction`,
       not used to filter here since Phase 1A does not size positions)
    - Neutral: no trades either direction

  Trend structure (checked per-ticker, mirrors the regime direction):
    - Long: price > 50-SMA AND 50-SMA > 200-SMA (no "or rising" grace clause, v1.3)
    - Short: price < 50-SMA AND 50-SMA < 200-SMA

  Leg & first-pullback definition (v1.4 -- swing-segmented, not cross-anchored):
    A "leg" begins at the most recent qualifying pullback low/high (or, if none
    exists yet in the current trend-structure regime, at the first bar where
    trend structure became true). A leg is confirmed once price makes a fresh
    extreme of >= 1.5*ATR(14) beyond the leg origin in the trend direction.
    The FIRST subsequent close that retraces >= 1.0*ATR(14) from that extreme,
    while price remains on the correct side of the 50-SMA, is the first
    pullback of that leg and is signal-eligible. Later retracements within the
    same leg are disqualified. Once a qualifying pullback resolves (price makes
    a fresh >=1.5*ATR extreme beyond the prior pullback low/high), a new leg
    begins and its first pullback becomes eligible again.

  Additional entry filters (all required):
    - Price inside or just touched the 9/20-EMA zone (deterministic, no
      "or recent swing structure" clause -- removed in v1.2)
    - RSI(14) between 40 and 60
    - ADX(14) >= 22
    - Pullback-bar volume < 20-day average volume (contraction)
    - Confirmation candle:
        Long:  close > prior high, OR (close in top 30% of range AND close > 9-EMA)
        Short: close < prior low,  OR (close in bottom 30% of range AND close < 9-EMA)
    - Calculated RR >= 3.0 (stop = pullback extreme +/- 0.2*ATR; target = 3R)
    - ATR% of price <= 6% (volatility filter)

Exit simulation (forward-scan from entry bar, max 15 bars per v1.4 time stop):
  - 'target' if close hits 3R (simplified single-target simulation for Phase 1A;
     the partial-exit-at-3R + trail-remainder mechanic from the hypothesis file
     is a live-execution detail, not modeled bar-by-bar here)
  - 'stop'   if close hits the stop price
  - 'time'   if neither hit within 15 bars

Earnings-date exclusion is NOT implemented in Phase 1A (no earnings-calendar
data source wired up yet) -- this is a known simplification, consistent with
the other Phase 1A scanners in this repo, and should be added before Phase 1B.

Dependencies: pandas, numpy only (SPY/VIX loaded from local parquet cache).
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "H_FIRST_PULLBACK_TREND_SWING"

MA_FAST = 50
MA_SLOW = 200
EMA_FAST = 9
EMA_SLOW = 20
ATR_PERIOD = 14
RSI_PERIOD = 14
ADX_PERIOD = 14
VOL_AVG_PERIOD = 20

MIN_ADX = 22
RSI_LOW, RSI_HIGH = 40, 60
LEG_EXTREME_ATR_MULT = 1.5     # impulsive move required to confirm a leg
PULLBACK_ATR_MULT = 1.0        # retracement required to qualify as a pullback
STOP_BUFFER_ATR_MULT = 0.2     # stop = pullback extreme +/- this * ATR
MIN_RR = 3.0
MAX_ATR_PCT = 0.06             # 6% volatility filter
MAX_BARS_HELD = 15              # v1.4 time stop
VIX_THRESHOLD = 25

_SPY_CACHE_PATH = Path.home() / ".hermes" / "market_data" / "SPY.parquet"
_VIX_CACHE_PATH = Path.home() / ".hermes" / "market_data" / "VIXINDEX.parquet"

# Module-level lazy singletons -- loaded once, reused across all scan() calls.
_REGIME_DF: "pd.DataFrame | None" = None


def _compute_rsi(close: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    """Wilder-smoothed RSI using EWM (alpha = 1/period)."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = ATR_PERIOD) -> pd.Series:
    """Wilder-smoothed ATR."""
    prior_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prior_close).abs(),
        (low - prior_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _compute_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = ADX_PERIOD) -> pd.Series:
    """Standard Wilder ADX."""
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    prior_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prior_close).abs(),
        (low - prior_close).abs(),
    ], axis=1).max(axis=1)

    atr = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    plus_dm_s = pd.Series(plus_dm, index=high.index).ewm(alpha=1.0 / period, adjust=False).mean()
    minus_dm_s = pd.Series(minus_dm, index=high.index).ewm(alpha=1.0 / period, adjust=False).mean()

    plus_di = 100 * (plus_dm_s / atr.replace(0, np.nan))
    minus_di = 100 * (minus_dm_s / atr.replace(0, np.nan))

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1.0 / period, adjust=False).mean()
    return adx


def _load_regime() -> pd.DataFrame:
    """Load & cache SPY+VIX regime series (lazy singleton), indexed by date."""
    global _REGIME_DF
    if _REGIME_DF is None:
        if not _SPY_CACHE_PATH.exists():
            raise FileNotFoundError(f"SPY cache not found: {_SPY_CACHE_PATH}")
        if not _VIX_CACHE_PATH.exists():
            raise FileNotFoundError(f"VIX cache not found: {_VIX_CACHE_PATH}")

        spy = pd.read_parquet(_SPY_CACHE_PATH)
        spy.columns = [c.lower() for c in spy.columns]
        spy = spy.sort_index()
        spy_close = spy["close"]
        spy_ma50 = spy_close.rolling(MA_FAST, min_periods=MA_FAST).mean()
        spy_ma200 = spy_close.rolling(MA_SLOW, min_periods=MA_SLOW).mean()

        vix = pd.read_parquet(_VIX_CACHE_PATH)
        vix.columns = [c.lower() for c in vix.columns]
        vix = vix.sort_index()
        vix_close = vix["close"].reindex(spy.index).ffill()

        risk_on = (spy_close > spy_ma50) & (spy_close > spy_ma200) & (vix_close < VIX_THRESHOLD)
        risk_off = (spy_close < spy_ma50) & (spy_close < spy_ma200)
        vix_size_reduction = risk_off & (vix_close >= VIX_THRESHOLD)

        _REGIME_DF = pd.DataFrame({
            "risk_on": risk_on,
            "risk_off": risk_off,
            "vix_size_reduction": vix_size_reduction,
        })
    return _REGIME_DF


def _subperiod(date) -> str:
    if pd.isna(date):
        return "unknown"
    d = date.date() if hasattr(date, "date") else date
    if d < pd.Timestamp("2019-04-01").date():
        return "pre_warmup"
    if d <= pd.Timestamp("2021-12-31").date():
        return "period1_bull"
    if d <= pd.Timestamp("2023-12-31").date():
        return "period2_bear"
    return "period3_current"


def _find_legs(close_arr, high_arr, low_arr, atr_arr, above50_arr, direction):
    """
    Walk the series once and tag each bar as a qualifying first-pullback bar
    or not, per the v1.4 swing-segmented leg definition.

    direction: 'long' or 'short'
    Returns: boolean numpy array, True where bar i is a qualifying first
    pullback of its leg (pullback extreme also returned via out params).
    """
    n = len(close_arr)
    is_first_pullback = np.zeros(n, dtype=bool)
    pullback_extreme = np.full(n, np.nan)   # the leg's extreme (swing high/low) for this pullback

    sign = 1 if direction == "long" else -1

    # State machine
    leg_origin_price = None      # price at leg origin
    leg_extreme_price = None     # best price achieved so far in this leg
    leg_extreme_idx = None
    leg_confirmed = False        # True once >=1.5*ATR extreme achieved from origin
    awaiting_new_leg = True      # True if we need a fresh origin (start, or after a pullback resolved)
    pullback_used_for_leg = False  # True once this leg's first pullback has been consumed

    for i in range(1, n):
        if np.isnan(atr_arr[i]) or atr_arr[i] <= 0:
            continue
        if not above50_arr[i]:
            # Trend structure broken -- reset everything, wait for structure to re-qualify
            awaiting_new_leg = True
            leg_origin_price = None
            leg_extreme_price = None
            leg_confirmed = False
            pullback_used_for_leg = False
            continue

        price = close_arr[i]
        extreme_price = high_arr[i] if direction == "long" else low_arr[i]

        if awaiting_new_leg:
            leg_origin_price = price
            leg_extreme_price = extreme_price
            leg_extreme_idx = i
            leg_confirmed = False
            pullback_used_for_leg = False
            awaiting_new_leg = False
            continue

        # Track running extreme since leg origin
        if sign * (extreme_price - leg_extreme_price) > 0:
            leg_extreme_price = extreme_price
            leg_extreme_idx = i
            # If we already used this leg's pullback and price makes a fresh
            # extreme beyond the prior pullback low/high, a new leg begins
            # (handled below via pullback_used_for_leg reset once retraced)

        atr_i = atr_arr[i]

        # Check if leg is confirmed (impulsive move of >= 1.5*ATR from origin)
        if not leg_confirmed:
            move = sign * (leg_extreme_price - leg_origin_price)
            if move >= LEG_EXTREME_ATR_MULT * atr_i:
                leg_confirmed = True

        if leg_confirmed and not pullback_used_for_leg:
            # Check for a qualifying retracement from the leg extreme
            retrace = sign * (leg_extreme_price - price)
            if retrace >= PULLBACK_ATR_MULT * atr_i:
                is_first_pullback[i] = True
                pullback_extreme[i] = leg_extreme_price
                pullback_used_for_leg = True
        elif leg_confirmed and pullback_used_for_leg:
            # A later retracement in the same leg -- disqualified by definition.
            # Check whether the trend has resumed and made a fresh extreme
            # beyond the leg_extreme_price -- if so, that resolves the pullback
            # and starts a new leg (origin = the point where pullback bottomed).
            move_beyond = sign * (extreme_price - leg_extreme_price)
            if move_beyond > 0:
                # Fresh extreme beyond prior leg's extreme -> new leg starts here
                leg_origin_price = leg_extreme_price
                leg_extreme_price = extreme_price
                leg_extreme_idx = i
                leg_confirmed = False
                pullback_used_for_leg = False
                # Re-check confirmation immediately using the fresh move
                move = sign * (leg_extreme_price - leg_origin_price)
                if move >= LEG_EXTREME_ATR_MULT * atr_i:
                    leg_confirmed = True

    return is_first_pullback, pullback_extreme


def _simulate_exit(df: pd.DataFrame, entry_idx: int, entry_price: float,
                    stop_price: float, target_price: float, direction: str) -> tuple:
    """
    Scan forward from the bar *after* entry_idx for up to MAX_BARS_HELD bars.
    Returns (exit_price, exit_reason, bars_held).
    """
    closes = df["close"].values
    n = len(closes)

    for offset in range(1, MAX_BARS_HELD + 1):
        idx = entry_idx + offset
        if idx >= n:
            last_idx = min(entry_idx + offset - 1, n - 1)
            return closes[last_idx], "time", offset
        c = closes[idx]
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

    exit_idx = min(entry_idx + MAX_BARS_HELD, n - 1)
    return closes[exit_idx], "time", MAX_BARS_HELD


def _scan_direction(df: pd.DataFrame, ticker: str, direction: str,
                     regime: pd.DataFrame) -> list:
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"] if "volume" in df.columns else None

    ma50 = close.rolling(MA_FAST, min_periods=MA_FAST).mean()
    ma200 = close.rolling(MA_SLOW, min_periods=MA_SLOW).mean()
    ema9 = close.ewm(span=EMA_FAST, adjust=False).mean()
    ema20 = close.ewm(span=EMA_SLOW, adjust=False).mean()
    atr = _compute_atr(high, low, close)
    rsi = _compute_rsi(close)
    adx = _compute_adx(high, low, close)
    vol_avg = volume.rolling(VOL_AVG_PERIOD, min_periods=VOL_AVG_PERIOD).mean() if volume is not None else None

    close_arr = close.values
    high_arr = high.values
    low_arr = low.values
    open_arr = df["open"].values if "open" in df.columns else close_arr
    ma50_arr = ma50.values
    ma200_arr = ma200.values
    ema9_arr = ema9.values
    ema20_arr = ema20.values
    atr_arr = atr.values
    rsi_arr = rsi.values
    adx_arr = adx.values
    vol_arr = volume.values if volume is not None else None
    vol_avg_arr = vol_avg.values if vol_avg is not None else None
    dates = df.index

    if direction == "long":
        above50_arr = (close_arr > ma50_arr) & (ma50_arr > ma200_arr)
    else:
        above50_arr = (close_arr < ma50_arr) & (ma50_arr < ma200_arr)

    is_first_pullback, pullback_extreme = _find_legs(
        close_arr, high_arr, low_arr, atr_arr, above50_arr, direction
    )

    # Align regime to this ticker's dates
    regime_aligned = regime.reindex(dates).ffill()
    risk_on_arr = regime_aligned["risk_on"].values
    risk_off_arr = regime_aligned["risk_off"].values
    vix_size_reduction_arr = regime_aligned["vix_size_reduction"].values

    min_start = max(MA_SLOW, ATR_PERIOD, VOL_AVG_PERIOD) + 1
    signals = []
    n = len(df)

    for i in range(min_start, n):
        if not is_first_pullback[i]:
            continue

        # Regime gate
        if direction == "long":
            if not bool(risk_on_arr[i]):
                continue
        else:
            if not bool(risk_off_arr[i]):
                continue

        if np.isnan(atr_arr[i]) or atr_arr[i] <= 0:
            continue

        # ATR% volatility filter
        atr_pct = atr_arr[i] / close_arr[i]
        if atr_pct > MAX_ATR_PCT:
            continue

        # RSI band
        if np.isnan(rsi_arr[i]) or not (RSI_LOW <= rsi_arr[i] <= RSI_HIGH):
            continue

        # ADX filter
        if np.isnan(adx_arr[i]) or adx_arr[i] < MIN_ADX:
            continue

        # EMA zone: price inside or just touched the 9/20-EMA band
        ema_lo = min(ema9_arr[i], ema20_arr[i])
        ema_hi = max(ema9_arr[i], ema20_arr[i])
        touch_tol = 0.005 * close_arr[i]  # 0.5% touch tolerance
        price_in_zone = (low_arr[i] - touch_tol <= ema_hi) and (high_arr[i] + touch_tol >= ema_lo)
        if not price_in_zone:
            continue

        # Volume contraction
        if vol_arr is not None and vol_avg_arr is not None:
            if np.isnan(vol_avg_arr[i]) or vol_arr[i] >= vol_avg_arr[i]:
                continue

        # Confirmation candle
        day_high, day_low, day_close = high_arr[i], low_arr[i], close_arr[i]
        day_range = day_high - day_low
        if day_range <= 0:
            continue
        pct_in_range = (day_close - day_low) / day_range

        if direction == "long":
            confirmed = (day_close > high_arr[i - 1]) or (pct_in_range >= 0.70 and day_close > ema9_arr[i])
        else:
            confirmed = (day_close < low_arr[i - 1]) or (pct_in_range <= 0.30 and day_close < ema9_arr[i])
        if not confirmed:
            continue

        # Risk/reward setup
        entry_price = day_close
        extreme = pullback_extreme[i]
        if np.isnan(extreme):
            continue

        stop_buffer = STOP_BUFFER_ATR_MULT * atr_arr[i]
        if direction == "long":
            stop_price = min(low_arr[i], entry_price) - stop_buffer
            risk = entry_price - stop_price
        else:
            stop_price = max(high_arr[i], entry_price) + stop_buffer
            risk = stop_price - entry_price

        if risk <= 0:
            continue
        if risk / entry_price < 0.005:
            continue

        if direction == "long":
            target_price = entry_price + MIN_RR * risk
        else:
            target_price = entry_price - MIN_RR * risk

        r_multiple_theoretical = MIN_RR  # by construction target is exactly 3R

        exit_price, exit_reason, bars_held = _simulate_exit(
            df, i, entry_price, stop_price, target_price, direction
        )
        if direction == "long":
            realised_r = (exit_price - entry_price) / risk
        else:
            realised_r = (entry_price - exit_price) / risk

        signal = {
            "ticker": ticker,
            "date": dates[i],
            "direction": direction,
            "entry_price": round(float(entry_price), 4),
            "stop_price": round(float(stop_price), 4),
            "target_price": round(float(target_price), 4),
            "exit_price": round(float(exit_price), 4),
            "exit_reason": exit_reason,
            "r_multiple": round(float(realised_r), 4),
            "bars_held": bars_held,
            "subperiod": _subperiod(dates[i]),
            "strategy_id": STRATEGY_ID,
            "adx": round(float(adx_arr[i]), 2),
            "rsi": round(float(rsi_arr[i]), 2),
            "vix_size_reduction": bool(vix_size_reduction_arr[i]) if direction == "short" else False,
        }
        signals.append(signal)

    return signals


def scan(df: pd.DataFrame, ticker: str) -> list:
    """
    Scan df for Strategy H -- High-RR First-Pullback Trend Swing (v1.4) signals,
    both long and short.
    """
    if ticker in ("SPY", "VIXINDEX", "^VIX"):
        return []  # regime benchmarks themselves are not traded

    df = df.copy()
    df.sort_index(inplace=True)
    if len(df) < max(MA_SLOW, ATR_PERIOD, VOL_AVG_PERIOD) + 10:
        return []

    regime = _load_regime()

    signals = []
    signals.extend(_scan_direction(df, ticker, "long", regime))
    signals.extend(_scan_direction(df, ticker, "short", regime))
    return signals


# ---------------------------------------------------------------------------
# __main__ -- quick smoke test on AAPL
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    data_path = Path.home() / ".hermes" / "market_data" / "AAPL.parquet"
    if not data_path.exists():
        print(f"[ERROR] Data file not found: {data_path}")
        sys.exit(1)

    print(f"Loading data from {data_path} ...")
    df = pd.read_parquet(data_path)
    df.columns = [c.lower() for c in df.columns]
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    print(f"Loaded {len(df)} rows  ({df.index[0].date()} -> {df.index[-1].date()})")

    results = scan(df, ticker="AAPL")
    print(f"\nStrategy H signals found: {len(results)}")

    if results:
        print("\nFirst 3 signals:")
        for sig in results[:3]:
            print("-" * 60)
            for k, v in sig.items():
                print(f"  {k:<20}: {v}")
    else:
        print("No signals detected.")
