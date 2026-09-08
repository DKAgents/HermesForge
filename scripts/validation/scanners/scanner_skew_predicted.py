#!/usr/bin/env python3
"""
scanner_skew_predicted.py — STR-SKEW-PRED: Predicted Skewness-Managed Factor

Built from CAND-20260908-skewness-managed-anomalies (Gong, Lynch & Ogden 2026).

Hypothesis: Cross-sectional forecasts of return skewness improve anomaly
portfolio performance by +5.45%/yr. Skewness is forecastable from:
  - size proxy (log price)
  - prior 6-month momentum
  - short-term momentum (1-month)
  - 20-day volatility
  - prior 60-day realized skewness

Implementation: Pre-computes per-ticker rolling characteristics once, then
scans monthly rebalance dates efficiently by looking up precomputed values.
Long top quintile by predicted skewness, short bottom quintile.
"""

import numpy as np
import pandas as pd

STRATEGY_ID = "SKEW_PREDICTED"

# ── Parameters ──────────────────────────────────────────────────────
SKEW_WINDOW = 63              # ~3 months trading days
REBALANCE_FREQ = 21            # Monthly rebalance (21 trading days)
QUINTILE = 5                   # Top/bottom quintile
ATR_PERIOD = 14
ATR_STOP_MULT = 2.0
MAX_BARS_HELD = 21             # Hold until next monthly rebalance
MIN_ASSETS = 20
MIN_FIT_SAMPLES = 30
FORECAST_HORIZON = 21          # ~1 month forward

# Characteristic windows
MOMENTUM_6M = 126
VOLATILITY_20D = 20
SHORT_MOM_1M = 21


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


def _compute_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    high, low = df["high"], df["low"]
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _precompute_characteristics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pre-compute rolling characteristics for a single ticker's DataFrame.

    Returns DataFrame indexed same as df with columns:
      size_proxy, momentum_6m, short_term_mom, volatility_20d,
      prior_skew (limited lookback), close, high, low, atr
    """
    close = df["close"]
    log_ret = np.log(close / close.shift(1))

    out = pd.DataFrame(index=df.index)

    # Size proxy: log price
    out["size_proxy"] = np.log(close.replace(0, np.nan))

    # Momentum: 6-month cumulative log return
    out["momentum_6m"] = log_ret.rolling(MOMENTUM_6M).sum()

    # Short-term momentum (1-month)
    out["short_term_mom"] = log_ret.rolling(SHORT_MOM_1M).sum()

    # Volatility (20-day std of log returns)
    out["volatility_20d"] = log_ret.rolling(VOLATILITY_20D).std()

    # Prior skewness (60-day)
    out["prior_skew"] = log_ret.rolling(SKEW_WINDOW).skew()

    # Cache OHLC for later
    out["close"] = close
    out["high"] = df["high"]
    out["low"] = df["low"]

    # ATR
    out["atr"] = _compute_atr(df)

    return out


def _predict_skewness(chars_row: pd.Series, coeffs: dict) -> float:
    """Apply fitted coefficients to predict next-period skewness."""
    pred = coeffs["intercept"]
    for feat in ["size_proxy", "momentum_6m", "short_term_mom", "volatility_20d", "prior_skew"]:
        pred += coeffs.get(feat, 0.0) * (chars_row.get(feat, np.nan) if isinstance(chars_row, pd.Series) else chars_row.get(feat, np.nan))
    return float(pred) if not np.isnan(pred) else np.nan


def scan(data: dict) -> list:
    """
    Cross-sectional batch scanner using PREDICTED skewness.

    Parameters
    ----------
    data : dict
        {ticker: DataFrame} mapping for all assets

    Returns
    -------
    list of dicts, one per signal
    """
    if not data or len(data) < MIN_ASSETS:
        return []

    # ── Phase 1: Pre-compute characteristics for every ticker ──
    print("  Pre-computing rolling characteristics...")
    char_cache = {}
    atr_cache = {}
    for ticker, df in data.items():
        if len(df) < SKEW_WINDOW + FORECAST_HORIZON + 10:
            continue
        ch = _precompute_characteristics(df)
        if ch is not None and len(ch) > SKEW_WINDOW:
            char_cache[ticker] = ch
            atr_cache[ticker] = ch["atr"]

    if len(char_cache) < MIN_ASSETS:
        return []

    # Collect all rebalance dates from the most common date range
    all_dates = set()
    for ch in char_cache.values():
        all_dates.update(ch.index)
    all_dates = sorted(all_dates)

    # Skip warmup period
    min_idx = SKEW_WINDOW + 10
    if len(all_dates) <= min_idx:
        return []
    start_date = all_dates[min_idx]
    trading_dates = [d for d in all_dates if d >= start_date]

    # Monthly rebalance dates
    rebalance_dates = trading_dates[::REBALANCE_FREQ]
    print(f"  {len(char_cache)} tickers, {len(rebalance_dates)} rebalance dates")

    # ── Phase 2: Rolling cross-sectional regression ──
    # Pre-compute realized_skewness as the FORECAST_HORIZON-forward skewness
    # (target variable: future skewness predicted from current characteristics)
    signals = []

    # Fit regression once per 12 months of data (avoids refitting at every date)
    REFIT_INTERVAL = 12 * REBALANCE_FREQ  # ~12 months
    coeffs_cache = {}

    for reb_idx, reb_date in enumerate(rebalance_dates):
        # ── 2a: Build cross-sectional snapshot at this date ──
        snapshot = {}
        for ticker, ch in char_cache.items():
            if reb_date not in ch.index:
                continue
            row = ch.loc[reb_date]

            # Check all characteristics are valid
            if pd.isna(row.get("size_proxy", np.nan)) or \
               pd.isna(row.get("momentum_6m", np.nan)) or \
               pd.isna(row.get("short_term_mom", np.nan)) or \
               pd.isna(row.get("volatility_20d", np.nan)) or \
               pd.isna(row.get("prior_skew", np.nan)):
                continue

            snapshot[ticker] = row

        if len(snapshot) < MIN_ASSETS:
            continue

        # ── 2b: Get coefficients (fit or cached) ──
        bucket = reb_idx // REFIT_INTERVAL
        if bucket not in coeffs_cache:
            # Build training set for regression: use current period's snapshot
            # to predict skewness FORECAST_HORIZON days ahead
            training_rows = []
            for ticker, ch in char_cache.items():
                if reb_date not in ch.index:
                    continue
                # Find the forward date
                date_pos = ch.index.get_loc(reb_date)
                if date_pos + FORECAST_HORIZON >= len(ch):
                    continue
                target_date = ch.index[date_pos + FORECAST_HORIZON]
                forward_row = ch.loc[target_date]
                if pd.isna(forward_row.get("prior_skew", np.nan)):
                    continue
                row = ch.loc[reb_date]
                if any(pd.isna(row.get(f, np.nan)) for f in
                       ["size_proxy", "momentum_6m", "short_term_mom", "volatility_20d", "prior_skew"]):
                    continue
                training_rows.append({
                    "realized_skewness": forward_row["prior_skew"],  # future skewness as target
                    "size_proxy": row["size_proxy"],
                    "momentum_6m": row["momentum_6m"],
                    "short_term_mom": row["short_term_mom"],
                    "volatility_20d": row["volatility_20d"],
                    "prior_skew": row["prior_skew"],
                })

            if len(training_rows) < MIN_FIT_SAMPLES:
                coeffs_cache[bucket] = {}
            else:
                train_df = pd.DataFrame(training_rows)
                coeffs_cache[bucket] = _fit_regression(train_df)

        coeffs = coeffs_cache[bucket]
        has_model = bool(coeffs)

        # ── 2c: Predict skewness for all stocks ──
        predictions = {}
        if has_model:
            for ticker, row in snapshot.items():
                pred = coeffs["intercept"]
                pred += coeffs.get("size_proxy", 0.0) * row["size_proxy"]
                pred += coeffs.get("momentum_6m", 0.0) * row["momentum_6m"]
                pred += coeffs.get("short_term_mom", 0.0) * row["short_term_mom"]
                pred += coeffs.get("volatility_20d", 0.0) * row["volatility_20d"]
                pred += coeffs.get("prior_skew", 0.0) * row["prior_skew"]
                if not np.isnan(pred):
                    predictions[ticker] = float(pred)
        else:
            # Fallback: use prior_skew directly as prediction
            for ticker, row in snapshot.items():
                val = row["prior_skew"]
                if not np.isnan(val):
                    predictions[ticker] = float(val)

        if len(predictions) < MIN_ASSETS:
            continue

        # ── 2d: Rank and select ──
        sorted_tickers = sorted(predictions.items(), key=lambda x: x[1])
        n = len(sorted_tickers)
        qsize = max(n // QUINTILE, 1)

        # Long TOP quintile (highest predicted skewness)
        long_tickers = [t for t, _ in sorted_tickers[-qsize:]]
        # Short BOTTOM quintile (lowest predicted skewness)
        short_tickers = [t for t, _ in sorted_tickers[:qsize]]

        # Next rebalance for time stop
        next_rebalance = rebalance_dates[reb_idx + 1] if reb_idx + 1 < len(rebalance_dates) else None

        # ── 3: Generate signals ──
        for ticker in long_tickers:
            sig = _create_signal(data, ticker, reb_date, "long",
                                 predictions[ticker], next_rebalance)
            if sig:
                signals.append(sig)

        for ticker in short_tickers:
            sig = _create_signal(data, ticker, reb_date, "short",
                                 predictions[ticker], next_rebalance)
            if sig:
                signals.append(sig)

    return signals


def _fit_regression(train_df: pd.DataFrame) -> dict:
    """
    OLS: realized_skewness ~ intercept + size_proxy + momentum_6m + short_term_mom
                              + volatility_20d + prior_skew
    """
    features = ["size_proxy", "momentum_6m", "short_term_mom", "volatility_20d", "prior_skew"]
    df = train_df.dropna(subset=["realized_skewness"] + features)
    if len(df) < MIN_FIT_SAMPLES:
        return {}

    X = np.column_stack([np.ones(len(df))] + [df[f].values for f in features])
    y = df["realized_skewness"].values

    try:
        xtx = X.T @ X
        if np.linalg.cond(xtx) > 1e10:
            return {}
        beta = np.linalg.solve(xtx, X.T @ y)
    except (np.linalg.LinAlgError, ValueError):
        return {}

    return dict(zip(["intercept"] + features, beta))


def _create_signal(data: dict, ticker: str, date: pd.Timestamp,
                   direction: str, pred_skew_val: float,
                   next_rebalance: pd.Timestamp) -> dict:
    """Create a signal dict for a specific ticker at a rebalance date."""
    df = data.get(ticker)
    if df is None:
        return None

    mask = df.index <= date
    if mask.sum() < ATR_PERIOD + 5:
        return None

    df_slice = df[mask]
    entry_idx = len(df_slice) - 1
    entry_price = float(df_slice["close"].iloc[-1])

    atr = _compute_atr(df_slice)
    atr_val = float(atr.iloc[-1])

    if atr_val <= 0 or entry_price <= 0:
        return None

    if direction == "long":
        stop_price = entry_price - ATR_STOP_MULT * atr_val
        risk = entry_price - stop_price
        target_price = entry_price + 2 * risk
    else:
        stop_price = entry_price + ATR_STOP_MULT * atr_val
        risk = stop_price - entry_price
        target_price = entry_price - 2 * risk

    if risk <= 1e-8:
        return None

    max_bars = MAX_BARS_HELD
    if next_rebalance is not None:
        bars_after = (df.index > date).sum()
        if 0 < bars_after < 60:
            max_bars = min(max_bars, bars_after)

    exit_price, exit_reason, bars_held = _simulate_exit(
        df, entry_idx, direction, entry_price, stop_price, max_bars
    )

    if direction == "long":
        realised_r = (exit_price - entry_price) / risk
    else:
        realised_r = (entry_price - exit_price) / risk

    return {
        "ticker": ticker,
        "date": date,
        "direction": direction,
        "entry_price": round(entry_price, 6),
        "stop_price": round(stop_price, 6),
        "target_price": round(target_price, 6),
        "exit_price": round(float(exit_price), 6),
        "exit_reason": exit_reason,
        "r_multiple": round(float(realised_r), 4),
        "bars_held": bars_held,
        "strategy_id": STRATEGY_ID,
        "predicted_skewness": round(pred_skew_val, 4),
        "subperiod": _subperiod(date),
        "rebalance": True,
    }


def _simulate_exit(df: pd.DataFrame, entry_idx: int, direction: str,
                   entry_price: float, stop_price: float,
                   max_bars: int) -> tuple:
    closes = df["close"].values
    highs = df["high"].values
    lows = df["low"].values
    n = len(closes)

    for offset in range(1, max_bars + 1):
        idx = entry_idx + offset
        if idx >= n:
            return closes[min(entry_idx + offset - 1, n - 1)], "time", offset
        if direction == "long":
            if lows[idx] <= stop_price:
                return stop_price, "stop", offset
        else:
            if highs[idx] >= stop_price:
                return stop_price, "stop", offset

    exit_idx = min(entry_idx + max_bars, n - 1)
    return closes[exit_idx], "time", max_bars


if __name__ == "__main__":
    import sys
    import pathlib

    print("Loading stock data...")
    repo_root = pathlib.Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(repo_root / "scripts" / "validation"))
    from fetch_data import load_all as load_all_stocks

    stocks = load_all_stocks()
    print(f"  {len(stocks)} symbols loaded")

    print("\nRunning STR-SKEW-PRED predicted skewness scanner...")
    signals = scan(stocks)

    if not signals:
        print("No signals generated.")
        sys.exit(0)

    r_values = [s["r_multiple"] for s in signals]
    long_sigs = [s for s in signals if s["direction"] == "long"]
    short_sigs = [s for s in signals if s["direction"] == "short"]
    wins = [s for s in signals if s["r_multiple"] > 0]

    avg_r = float(np.mean(r_values))
    win_rate = len(wins) / len(signals) if signals else 0
    avg_win = float(np.mean([s["r_multiple"] for s in wins])) if wins else 0
    avg_loss = float(np.mean([s["r_multiple"] for s in signals if s["r_multiple"] <= 0])) or 0

    print(f"\nSTR-SKEW-PRED Phase 1A Results (Stocks):")
    print(f"  Signals: {len(signals)} ({len(long_sigs)} long, {len(short_sigs)} short)")
    print(f"  Avg R: {avg_r:+.4f}")
    print(f"  Win rate: {win_rate:.1%}")
    print(f"  Avg win: {avg_win:+.4f} | Avg loss: {avg_loss:+.4f}")

    long_r = [s["r_multiple"] for s in long_sigs]
    short_r = [s["r_multiple"] for s in short_sigs]
    print(f"\n  Long only:  {len(long_r):3d} sigs, avg R = {float(np.mean(long_r)):+.4f}")
    print(f"  Short only: {len(short_r):3d} sigs, avg R = {float(np.mean(short_r)):+.4f}")

    by_year = {}
    for s in signals:
        yr = str(s["date"])[:4]
        by_year.setdefault(yr, []).append(s["r_multiple"])
    print(f"\n  By year:")
    for yr in sorted(by_year.keys()):
        yr_r = by_year[yr]
        print(f"    {yr}: {len(yr_r):3d} sigs, avg R = {float(np.mean(yr_r)):+.4f}")