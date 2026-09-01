#!/usr/bin/env python3
"""
scanner_global_yield_surge.py — STR-YIELD-SURGE: Global Bond Yield Surge Risk Reduction

Edge candidate: CAND-20260901-global-bond-yield-surge
Source hypothesis: Global bond yields surging to 2008 highs represent a regime
transition from "debasement" to "tightening." When US 10Y yield rises sharply,
equity risk premium is negatively skewed — tech (QQQ) takes the hardest hit,
and defensive sectors (XLP, XLU) provide relative safety.

Signal Rules:
  Regime trigger (daily, from cached TNX / VIXINDEX / DXY data):
    1. TNX yield (US 10Y) risen >= YIELD_RISE over YIELD_LOOKBACK days
    2. VIX rising: VIX change > VIX_RISE_PCT over same window (fear confirmation)
    3. Optional: DXY > DXY_SMA (dollar strengthening confirms tightening)

  When regime active → SHORT QQQ (tech most exposed to rising yields):
    - Entry: At close on regime trigger bar
    - Stop: ATR-based (stop above entry at ATR_STOP_MULT * ATR)
    - Target: MIN_RR * risk
    - Max hold: MAX_BARS_HELD (default 20 trading days ~ 1 month)

  Also generate LONG signals on XLP, XLU (defensive rotation) when regime active.

Dependencies: pandas, numpy. TNX/VIXINDEX/DXY loaded from parquet cache
(~/.hermes/market_data/). Stock ETFs from main data dict.
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "STR-YIELD-SURGE"

# ── Parameters (module-level, monkey-patchable for walk-forward) ──────────────
YIELD_LOOKBACK = 15           # Days over which to measure yield rise (~2 weeks)
YIELD_RISE = 0.35             # 10Y yield must rise >= this many pp over lookback (0.35 = 35 bps)
VIX_RISE_PCT = 3.0           # VIX must rise >= this % over same window (fear confirmation)
DXY_SMA_PERIOD = 20          # Optional: DXY > this SMA for tightening confirmation
ATR_PERIOD = 14
ATR_STOP_MULT = 2.0
MIN_RR = 1.5
MAX_BARS_HELD = 20           # ~1 month
REENTRY_COOLDOWN = 10         # Min bars between signals

# Targets
SHORT_TICKERS = ["QQQ"]       # Tech most exposed to rising yields
LONG_TICKERS = ["XLP", "XLU"]  # Defensive rotation (staples, utilities)

# Cache
_CACHE_DIR = Path.home() / ".hermes" / "market_data"

# Cached regime series
_REGIME_SERIES = None
_REGIME_KEY = None


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


def _compute_atr(high, low, close, period=ATR_PERIOD):
    prior_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prior_close).abs(),
        (low - prior_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _load_series(ticker: str, col: str = "close") -> pd.Series:
    """Load a cached parquet and return the specified column as a Series."""
    p = _CACHE_DIR / f"{ticker}.parquet"
    if not p.exists():
        return pd.Series(dtype=float)
    df = pd.read_parquet(p)
    df.columns = [c.lower() for c in df.columns]
    df = df.sort_index()
    return df[col] if col in df.columns else df.iloc[:, 0]


def _load_regime() -> pd.Series:
    """
    Build a date-indexed boolean Series: yield_surge_regime_active.

    Conditions:
      1. TNX yield risen >= YIELD_RISE over YIELD_LOOKBACK days
      2. VIX risen >= VIX_RISE_PCT % over same window (fear confirmation)
      3. (Optional) DXY > 20-day SMA (dollar strength = tightening)
    """
    global _REGIME_SERIES, _REGIME_KEY
    key = (YIELD_LOOKBACK, YIELD_RISE, VIX_RISE_PCT, DXY_SMA_PERIOD)
    if _REGIME_SERIES is not None and _REGIME_KEY == key:
        return _REGIME_SERIES

    tnx = _load_series("TNX")
    vix = _load_series("VIXINDEX")
    dxy = _load_series("DXY")

    # Require at least TNX and VIX
    if tnx.empty or vix.empty:
        _REGIME_SERIES = pd.Series(False, index=pd.DatetimeIndex([]))
        _REGIME_KEY = key
        return _REGIME_SERIES

    # Align to common index
    common_idx = tnx.index.intersection(vix.index)
    if not dxy.empty:
        common_idx = common_idx.intersection(dxy.index)

    tnx = tnx.reindex(common_idx).ffill()
    vix = vix.reindex(common_idx).ffill()
    dxy = dxy.reindex(common_idx).ffill() if not dxy.empty else pd.Series(index=common_idx, dtype=float)

    # Condition 1: TNX yield has risen >= YIELD_RISE over YIELD_LOOKBACK days
    tnx_change = tnx - tnx.shift(YIELD_LOOKBACK)
    cond_yield_surge = tnx_change >= YIELD_RISE

    # Condition 2: VIX fear confirmation (rising)
    vix_change = (vix - vix.shift(YIELD_LOOKBACK)) / vix.shift(YIELD_LOOKBACK) * 100
    cond_vix_fear = vix_change >= VIX_RISE_PCT

    # Condition 3: DXY > 20-day SMA (dollar strength = tightening regime)
    cond_dxy = pd.Series(True, index=common_idx)
    if not dxy.empty and len(dxy) > DXY_SMA_PERIOD + 5:
        dxy_sma20 = dxy.rolling(DXY_SMA_PERIOD, min_periods=DXY_SMA_PERIOD).mean()
        cond_dxy = dxy > dxy_sma20

    # All conditions
    regime = cond_yield_surge & cond_vix_fear & cond_dxy
    regime = regime.fillna(False)

    # Filter to valid signal period (post 2019-04-01)
    regime = regime[regime.index >= pd.Timestamp("2019-04-01")]

    _REGIME_SERIES = regime
    _REGIME_KEY = key
    return _REGIME_SERIES


def _simulate_exit(closes: np.ndarray, entry_idx: int, entry_price: float,
                   stop_price: float, target_price: float,
                   direction: str = "long", max_bars: int = MAX_BARS_HELD):
    """Simulate forward exit: stop, target, or time.
    
    closes: full array of close prices for the ticker.
    entry_idx: index position in closes where entry occurs.
    """
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


def scan(data: dict) -> list:
    """
    Batch scanner. Takes the full stock data dict.
    Uses TNX/VIXINDEX/DXY for regime detection, generates signals on sector ETFs.

    When yield-surge regime is active:
      - SHORT QQQ (tech most exposed)
      - LONG XLP, XLU (defensive rotation)
    """
    regime = _load_regime()
    if regime.empty:
        return []

    # Pre-sort all dataframes by index and lowercase columns
    clean_data = {}
    for ticker, df in data.items():
        d = df.copy()
        d.columns = [c.lower() for c in d.columns]
        d.sort_index(inplace=True)
        clean_data[ticker] = d

    # Get regime dates that are also in the data's date range
    all_stock_dates = set()
    for df in clean_data.values():
        all_stock_dates.update(df.index)
    all_stock_dates = sorted(all_stock_dates)

    # Build a mapping from date -> array index for each ticker that has the date
    # We need this so _simulate_exit can look forward from the entry position.
    date_to_idx = {}
    for ticker, df in clean_data.items():
        date_to_idx[ticker] = {d: i for i, d in enumerate(df.index)}

    min_start = max(ATR_PERIOD, YIELD_LOOKBACK) + 5
    signals = []
    last_signal_date = None

    for date_idx, current_date in enumerate(all_stock_dates):
        if date_idx < min_start:
            continue

        # Check regime on this date
        if current_date not in regime.index:
            # Find nearest prior regime value
            prior = regime[regime.index <= current_date]
            if prior.empty:
                continue
            regime_active = bool(prior.iloc[-1])
        else:
            regime_active = bool(regime.loc[current_date])

        if not regime_active:
            continue

        # Cooldown
        if last_signal_date is not None:
            days_since = (pd.Timestamp(current_date) - pd.Timestamp(last_signal_date)).days
            if days_since < REENTRY_COOLDOWN:
                continue

        # --- SHORT signals ---
        for ticker in SHORT_TICKERS:
            df = clean_data.get(ticker)
            if df is None or len(df) < min_start + 10:
                continue

            tix = date_to_idx.get(ticker)
            if tix is None or current_date not in tix:
                continue
            entry_idx = tix[current_date]
            if entry_idx < min_start:
                continue

            entry_price = float(df["close"].iloc[entry_idx])

            # Compute ATR up to and including this bar
            atr_series = _compute_atr(df["high"].iloc[:entry_idx + 1],
                                      df["low"].iloc[:entry_idx + 1],
                                      df["close"].iloc[:entry_idx + 1])
            atr_val = float(atr_series.iloc[-1])
            if atr_val <= 0 or np.isnan(atr_val):
                continue

            # Short: stop above entry, target below
            stop_price = entry_price + ATR_STOP_MULT * atr_val
            risk = stop_price - entry_price
            if risk <= 0 or risk / entry_price < 0.002:
                continue
            target_price = entry_price - MIN_RR * risk

            closes = df["close"].values.astype(float)
            ep, er, bh = _simulate_exit(
                closes, entry_idx, entry_price, stop_price, target_price,
                direction="short"
            )
            r_mult = (entry_price - ep) / risk

            signals.append({
                "ticker": ticker,
                "date": current_date,
                "direction": "short",
                "entry_price": round(entry_price, 4),
                "stop_price": round(float(stop_price), 4),
                "target_price": round(float(target_price), 4),
                "exit_price": round(float(ep), 4),
                "exit_reason": er,
                "r_multiple": round(float(r_mult), 4),
                "bars_held": bh,
                "strategy_id": STRATEGY_ID,
                "subperiod": _subperiod(pd.Timestamp(current_date)),
                "regime": "yield_surge",
                "entry_type": "yield_regime",
            })

        # --- LONG (defensive) signals ---
        for ticker in LONG_TICKERS:
            df = clean_data.get(ticker)
            if df is None or len(df) < min_start + 10:
                continue

            tix = date_to_idx.get(ticker)
            if tix is None or current_date not in tix:
                continue
            entry_idx = tix[current_date]
            if entry_idx < min_start:
                continue

            entry_price = float(df["close"].iloc[entry_idx])

            atr_series = _compute_atr(df["high"].iloc[:entry_idx + 1],
                                      df["low"].iloc[:entry_idx + 1],
                                      df["close"].iloc[:entry_idx + 1])
            atr_val = float(atr_series.iloc[-1])
            if atr_val <= 0 or np.isnan(atr_val):
                continue

            # Long: stop below entry, target above
            stop_price = entry_price - ATR_STOP_MULT * atr_val
            risk = entry_price - stop_price
            if risk <= 0 or risk / entry_price < 0.002:
                continue
            target_price = entry_price + MIN_RR * risk

            closes = df["close"].values.astype(float)
            ep, er, bh = _simulate_exit(
                closes, entry_idx, entry_price, stop_price, target_price,
                direction="long"
            )
            r_mult = (ep - entry_price) / risk

            signals.append({
                "ticker": ticker,
                "date": current_date,
                "direction": "long",
                "entry_price": round(entry_price, 4),
                "stop_price": round(float(stop_price), 4),
                "target_price": round(float(target_price), 4),
                "exit_price": round(float(ep), 4),
                "exit_reason": er,
                "r_multiple": round(float(r_mult), 4),
                "bars_held": bh,
                "strategy_id": STRATEGY_ID,
                "subperiod": _subperiod(pd.Timestamp(current_date)),
                "regime": "yield_surge",
                "entry_type": "yield_defensive",
            })

        if signals:
            last_signal_date = current_date

    return signals


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from fetch_data import load_all

    print("Loading stock data...")
    stocks = load_all()
    print(f"  {len(stocks)} tickers loaded")

    print("\nRunning STR-YIELD-SURGE global bond yield surge scanner...")
    signals = scan(stocks)

    if not signals:
        print("No signals generated (regime may not have triggered historically).")
        sys.exit(0)

    r_values = [s["r_multiple"] for s in signals]
    short_sigs = [s for s in signals if s["direction"] == "short"]
    long_sigs = [s for s in signals if s["direction"] == "long"]
    wins = [s for s in signals if s["r_multiple"] > 0]

    avg_r = np.mean(r_values)
    win_rate = len(wins) / len(signals) if signals else 0

    print(f"\nSTR-YIELD-SURGE Phase 1A Results:")
    print(f"  Signals: {len(signals)} ({len(long_sigs)} long, {len(short_sigs)} short)")
    print(f"  Avg R: {avg_r:+.4f}")
    print(f"  Win rate: {win_rate:.1%}")
    if wins:
        print(f"  Avg win: {np.mean([s['r_multiple'] for s in wins]):+.4f}")
    if len(r_values) - len(wins) > 0:
        losses = [s for s in signals if s["r_multiple"] <= 0]
        print(f"  Avg loss: {np.mean([s['r_multiple'] for s in losses]):+.4f}")

    by_year = {}
    for s in signals:
        yr = str(s["date"])[:4]
        if yr not in by_year:
            by_year[yr] = []
        by_year[yr].append(s["r_multiple"])

    print(f"\n  By year:")
    for yr in sorted(by_year.keys()):
        yr_r = by_year[yr]
        print(f"    {yr}: {len(yr_r):3d} sigs, avg R = {np.mean(yr_r):+.4f}")