#!/usr/bin/env python3
"""
scanner_narrowing_leadership_breadth.py — Narrowing Leadership Breadth Divergence

Built from CAND-20260913-narrowing-leadership-breadth.

Hypothesis:
  When the RSP/SPY ratio (equal-weight vs cap-weight S&P 500) declines below
  its 10-week moving average AND the week-over-week change is negative, the
  market is in a "narrowing leadership" regime. In this regime, gains are
  concentrated in the largest names, the tape is fragile, and forward returns
  for broad-market ETFs are expected to be below-average or negative.

Signal Rules:
  1. Compute RSP/SPY ratio daily.
  2. Compute trailing 10-week (50-bar) SMA of the ratio.
  3. Signal triggers when:
     - RSP/SPY ratio < 10-week SMA AND
     - RSP/SPY ratio week-over-week change is negative
  4. When active: short SPY (cap-weighted broad market vulnerable).
  5. Exit at 5 bars (time stop) or 2x ATR stop.

This is a "batch" scanner — takes the full stock data dict but also
independently loads/fetches RSP data (not in standard universe).

Dependencies: pandas, numpy, yfinance (for RSP fetch only).
"""

import os
import sys
import time
import pathlib
import numpy as np
import pandas as pd

STRATEGY_ID = "NARROW_LEAD_BREADTH"

# ── Parameters (parameterizable) ────────────────────────────────────────────
SMA_WINDOW = 50              # 10 trading weeks ≈ 50 bars
REBALANCE_FREQ = 5            # Rebalance weekly (every 5 bars)
ATR_PERIOD = 14
ATR_STOP_MULT = 2.0
MAX_BARS_HELD = 5             # Time stop: 5 days forward return
MIN_SIGNAL_WINDOWS = 50       # Candidate says minimum 50 signal windows

# RSP cache (independent of main universe)
RSP_CACHE_DIR = pathlib.Path.home() / ".hermes" / "rsp_cache"


def _cache_rsp_path() -> pathlib.Path:
    RSP_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return RSP_CACHE_DIR / "RSP.parquet"


def _fetch_and_cache_rsp() -> pd.DataFrame | None:
    """Fetch RSP via yfinance, cache as parquet, return DataFrame."""
    try:
        import yfinance as yf
        df = yf.download("RSP", start="2018-10-01", progress=False)
        if df is None or df.empty:
            return None
        df.index = pd.to_datetime(df.index)
        # Flatten MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        out_path = _cache_rsp_path()
        df.to_parquet(out_path)
        print(f"  [RSP] Fetched & cached: {len(df)} bars → {out_path}")
        return df
    except Exception as e:
        print(f"  [RSP] ERROR fetching: {e}")
        return None


def _load_rsp() -> pd.DataFrame | None:
    """Load RSP from cache, fetching if needed."""
    p = _cache_rsp_path()
    if p.exists():
        # Check age — re-fetch if >1 day old
        age = time.time() - p.stat().st_mtime
        if age < 86400:
            df = pd.read_parquet(p)
            print(f"  [RSP] Loaded {len(df)} bars from cache")
            return df
    return _fetch_and_cache_rsp()


def _load_or_get_rsp_from_data(data: dict) -> pd.DataFrame | None:
    """Try to get RSP from data dict first, else load from cache/fetch."""
    if "RSP" in data:
        return data["RSP"]
    return _load_rsp()


def _subperiod(date) -> str:
    """Classify a date into ADR-004 sub-periods."""
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
    """Average True Range."""
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _detect_narrowing_leadership(
    rsp: pd.DataFrame,
    spy: pd.DataFrame,
    date: pd.Timestamp,
) -> tuple[bool, float, float, float]:
    """
    Detect narrowing leadership regime at a given date.

    Returns (signal_active, rsp_spy_ratio, ratio_sma, ratio_weekly_change).
    """
    rsp_mask = rsp.index <= date
    spy_mask = spy.index <= date

    rsp_slice = rsp[rsp_mask]
    spy_slice = spy[spy_mask]

    if len(rsp_slice) < SMA_WINDOW + 5 or len(spy_slice) < SMA_WINDOW + 5:
        return False, np.nan, np.nan, np.nan

    # Align on common dates
    rsp_close = rsp_slice["close"].reindex(spy_slice.index, method="ffill")
    spy_close = spy_slice["close"]

    # RSP/SPY ratio
    ratio = rsp_close / spy_close

    # 10-week SMA
    ratio_sma = ratio.rolling(window=SMA_WINDOW, min_periods=SMA_WINDOW).mean()

    # Current values
    current_ratio = float(ratio.iloc[-1])
    current_sma = float(ratio_sma.iloc[-1])

    if np.isnan(current_sma):
        return False, current_ratio, current_sma, np.nan

    # Ratio < SMA?
    ratio_below_sma = current_ratio < current_sma

    # Week-over-week change (5 trading days ago)
    if len(ratio) >= 6:
        ratio_5d_ago = float(ratio.iloc[-6])
        weekly_change = (current_ratio - ratio_5d_ago) / ratio_5d_ago
    else:
        weekly_change = 0.0

    weekly_declining = weekly_change < 0

    signal_active = ratio_below_sma and weekly_declining
    return signal_active, current_ratio, current_sma, weekly_change


def _simulate_exit(df: pd.DataFrame, entry_idx: int, direction: str,
                   entry_price: float, stop_price: float,
                   max_bars: int) -> tuple:
    """Simulate exit via stop loss or time stop."""
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


def scan(data: dict) -> list:
    """
    Batch scanner: detect narrowing-leadership regime and generate signals.

    Parameters
    ----------
    data : dict
        {ticker: DataFrame} for all stock tickers. Must include SPY and QQQ.

    Returns
    -------
    list of dict, one per signal (short SPY, short QQQ when regime active)
    """
    # Need SPY from data
    spy = data.get("SPY")
    if spy is None:
        print("  [SCANNER] SPY not found in data dict — cannot compute signal")
        return []

    # Load RSP independently
    rsp = _load_or_get_rsp_from_data(data)
    if rsp is None:
        print("  [SCANNER] RSP not available — cannot compute narrowing-leadership signal")
        return []

    # Get QQQ too for secondary signals
    qqq = data.get("QQQ")

    # Filter to valid signal period
    valid_start = pd.Timestamp("2019-04-01")
    spy = spy[spy.index >= valid_start].copy()
    if qqq is not None:
        qqq = qqq[qqq.index >= valid_start].copy()

    if len(spy) < SMA_WINDOW + 10:
        print("  [SCANNER] Insufficient SPY history")
        return []

    # Get all dates from SPY (index we'll trade)
    all_dates = sorted(spy.index)

    # Rebalance dates (weekly)
    rebalance_dates = all_dates[::REBALANCE_FREQ]

    signals = []

    for rebalance_idx, rebalance_date in enumerate(rebalance_dates):
        # Detect regime at this date
        signal_active, ratio_val, sma_val, weekly_chg = _detect_narrowing_leadership(
            rsp, spy, rebalance_date
        )

        if not signal_active:
            continue

        # ── Generate signal: SHORT SPY ──────────────────────────────────
        spy_mask = spy.index <= rebalance_date
        spy_slice = spy[spy_mask]
        entry_idx = len(spy_slice) - 1

        entry_price = float(spy_slice["close"].iloc[-1])
        if entry_price <= 0:
            continue

        # ATR at entry
        atr = _compute_atr(spy_slice)
        atr_val = float(atr.iloc[-1])
        if atr_val <= 0:
            continue

        # Short SPY: stop above entry
        stop_price = entry_price + ATR_STOP_MULT * atr_val
        risk = stop_price - entry_price
        target_price = entry_price - 2 * risk

        if risk <= 0:
            continue

        # Time stop: 5 days
        max_bars = MAX_BARS_HELD
        after_mask = spy.index > rebalance_date
        bars_after = after_mask.sum()
        if 0 < bars_after < 60:
            max_bars = min(max_bars, bars_after)

        # Simulate exit
        exit_price, exit_reason, bars_held = _simulate_exit(
            spy, entry_idx, "short", entry_price, stop_price, max_bars
        )

        # R-multiple for short
        realised_r = (entry_price - exit_price) / risk

        signals.append({
            "ticker": "SPY",
            "date": rebalance_date,
            "direction": "short",
            "entry_price": round(entry_price, 6),
            "stop_price": round(stop_price, 6),
            "target_price": round(target_price, 6),
            "exit_price": round(float(exit_price), 6),
            "exit_reason": exit_reason,
            "r_multiple": round(float(realised_r), 4),
            "bars_held": bars_held,
            "strategy_id": STRATEGY_ID,
            "rsp_spy_ratio": round(ratio_val, 6),
            "ratio_sma": round(sma_val, 6),
            "weekly_change": round(weekly_chg, 6),
            "subperiod": _subperiod(rebalance_date),
            "rebalance": True,
        })

        # ── If QQQ available, also generate SHORT QQQ signal ─────────────
        if qqq is not None:
            qqq_mask = qqq.index <= rebalance_date
            qqq_slice = qqq[qqq_mask]
            qqq_entry_idx = len(qqq_slice) - 1
            qqq_entry_price = float(qqq_slice["close"].iloc[-1])

            if qqq_entry_price > 0:
                qqq_atr = _compute_atr(qqq_slice)
                qqq_atr_val = float(qqq_atr.iloc[-1])
                if qqq_atr_val > 0:
                    qqq_stop = qqq_entry_price + ATR_STOP_MULT * qqq_atr_val
                    qqq_risk = qqq_stop - qqq_entry_price
                    qqq_target = qqq_entry_price - 2 * qqq_risk

                    if qqq_risk > 0:
                        qqq_exit, qqq_exit_reason, qqq_bars = _simulate_exit(
                            qqq, qqq_entry_idx, "short", qqq_entry_price, qqq_stop, max_bars
                        )
                        qqq_r = (qqq_entry_price - qqq_exit) / qqq_risk

                        signals.append({
                            "ticker": "QQQ",
                            "date": rebalance_date,
                            "direction": "short",
                            "entry_price": round(qqq_entry_price, 6),
                            "stop_price": round(qqq_stop, 6),
                            "target_price": round(qqq_target, 6),
                            "exit_price": round(float(qqq_exit), 6),
                            "exit_reason": qqq_exit_reason,
                            "r_multiple": round(float(qqq_r), 4),
                            "bars_held": qqq_bars,
                            "strategy_id": STRATEGY_ID,
                            "rsp_spy_ratio": round(ratio_val, 6),
                            "ratio_sma": round(sma_val, 6),
                            "weekly_change": round(weekly_chg, 6),
                            "subperiod": _subperiod(rebalance_date),
                            "rebalance": True,
                        })

        # ── Also generate LONG RSP signal (betting on reversion) ────────
        rsp_mask = rsp.index <= rebalance_date
        rsp_slice = rsp[rsp_mask]
        rsp_entry_idx = len(rsp_slice) - 1
        rsp_entry_price = float(rsp_slice["close"].iloc[-1])

        if rsp_entry_price > 0:
            rsp_atr = _compute_atr(rsp_slice)
            rsp_atr_val = float(rsp_atr.iloc[-1])
            if rsp_atr_val > 0:
                rsp_stop = rsp_entry_price - ATR_STOP_MULT * rsp_atr_val
                rsp_risk = rsp_entry_price - rsp_stop
                rsp_target = rsp_entry_price + 2 * rsp_risk

                if rsp_risk > 0:
                    rsp_exit, rsp_exit_reason, rsp_bars = _simulate_exit(
                        rsp, rsp_entry_idx, "long", rsp_entry_price, rsp_stop, max_bars
                    )
                    rsp_r = (rsp_exit - rsp_entry_price) / rsp_risk

                    signals.append({
                        "ticker": "RSP",
                        "date": rebalance_date,
                        "direction": "long",
                        "entry_price": round(rsp_entry_price, 6),
                        "stop_price": round(rsp_stop, 6),
                        "target_price": round(rsp_target, 6),
                        "exit_price": round(float(rsp_exit), 6),
                        "exit_reason": rsp_exit_reason,
                        "r_multiple": round(float(rsp_r), 4),
                        "bars_held": rsp_bars,
                        "strategy_id": STRATEGY_ID,
                        "rsp_spy_ratio": round(ratio_val, 6),
                        "ratio_sma": round(sma_val, 6),
                        "weekly_change": round(weekly_chg, 6),
                        "subperiod": _subperiod(rebalance_date),
                        "rebalance": True,
                    })

    print(f"  [SCANNER] Generated {len(signals)} signals across {len(rebalance_dates)} rebalance dates")
    return signals


if __name__ == "__main__":
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "scripts" / "validation"))
    from fetch_data import load_all as load_all_stocks

    print("Loading stock data (stocks universe)...")
    stocks = load_all_stocks()
    print(f"  {len(stocks)} tickers loaded")
    print(f"  SPY in data: {'SPY' in stocks}")
    print(f"  QQQ in data: {'QQQ' in stocks}")

    print("\nRunning narrowing leadership breadth scanner...")
    signals = scan(stocks)

    if not signals:
        print("No signals generated.")
        sys.exit(0)

    r_values = [s["r_multiple"] for s in signals]
    wins = [s for s in signals if s["r_multiple"] > 0]

    avg_r = np.mean(r_values)
    win_rate = len(wins) / len(signals)
    avg_win = np.mean([s["r_multiple"] for s in wins]) if wins else 0
    avg_loss = np.mean([s["r_multiple"] for s in signals if s["r_multiple"] <= 0]) or 0

    print(f"\nSTR-NARROW-LEAD-BREADTH Phase 1A Results:")
    print(f"  Signals: {len(signals)}")
    print(f"  Avg R: {avg_r:+.4f}")
    print(f"  Win rate: {win_rate:.1%}")
    print(f"  Avg win: {avg_win:+.4f} | Avg loss: {avg_loss:+.4f}")

    # By year
    by_year = {}
    for s in signals:
        yr = str(s["date"])[:4]
        by_year.setdefault(yr, []).append(s["r_multiple"])
    print(f"\n  By year:")
    for yr in sorted(by_year.keys()):
        yr_r = by_year[yr]
        print(f"    {yr}: {len(yr_r):3d} sigs, avg R = {np.mean(yr_r):+.4f}")

    # By ticker
    by_ticker = {}
    for s in signals:
        t = s["ticker"]
        by_ticker.setdefault(t, []).append(s["r_multiple"])
    print(f"\n  By ticker:")
    for t in sorted(by_ticker.keys()):
         t_r = by_ticker[t]
         print(f"    {t}: {len(t_r):3d} sigs, avg R = {np.mean(t_r):+.4f}")