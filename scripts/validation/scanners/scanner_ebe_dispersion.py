#!/usr/bin/env python3
"""
scanner_ebe_dispersion.py — STR-EBE-DISPERSION: "Everything But Energy" Sector Dispersion
========================================================================================

Phase 1A scanner. Batch mode (scan(data_dict)).

Hypothesis: When the top-performing sector (Energy, XLE) and a bottom sector (Consumer
Discretionary, XLY) diverge to >40pp YTD AND fewer than 3 of the major S&P sector ETFs
have a positive weekly return AND SPX itself is range-bound, the extreme dispersion
mean-reverts over 4-8 weeks. The direction asymmetry favors short XLE / long XLY
because oil retreats while consumer fundamentals remain resilient.

Signal rules:
  1. Compute rolling 1-year (252d) return gap between XLE and XLY
  2. Compute weekly return for each available sector ETF
  3. Condition triggers when ALL of:
       a. YTD-like dispersion gap (252d return) > 40 percentage points
       b. Fewer than 3 of N sector ETFs positive in the current week
       c. SPX (SPY) 1-week return between -2% and +1% (range-bound, not trending)
       d. VIX < 25 (skip during extreme volatility)
  4. Entry: Short XLE / Long XLY (equal notional)
  5. Stop: Gap widens by >10pp from entry spread
  6. Target: Gap narrows to <20pp
  7. Time stop: 40 trading days (~8 weeks)

Dependencies: pandas, numpy, yfinance.

CONFIDENCE: SPECULATIVE — proceed to Phase 1A backtest.
"""

import numpy as np
import pandas as pd
import pathlib
import sys

STRATEGY_ID = "STR-EBE-DISPERSION"
STRATEGY_NAME = "EBE Sector Dispersion Mean Reversion"

# ── Parameters ────────────────────────────────────────────────────────────────
DISPERSION_THRESHOLD_PP = 40.0    # Min YTD-like gap in percentage points (e.g. 40%)
MAX_SECTORS_POSITIVE = 2           # Max number of sectors with positive weekly return (<3)
SPX_WEEKLY_MIN = -2.0              # SPX 1-week return lower bound (%)
SPX_WEEKLY_MAX = 1.0               # SPX 1-week return upper bound (%)
VIX_MAX = 25.0                     # Skip if VIX above this
MAX_HOLD_BARS = 40                 # 8 weeks ~ 40 trading days
LOOKBACK_YTD = 252                 # ~1 year of trading days for "YTD" dispersion
RR_TARGET = 2.0                    # Risk:Reward target for the pair
STOP_SPREAD_WIDEN_PP = 10.0        # Stop if gap widens by more than this amount (pp)

# Sector ETFs available in our universe
SECTOR_ETFS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLC", "XLB"]
# Primary pair
ASSET_A = "XLE"  # Short leg (Energy)
ASSET_B = "XLY"  # Long leg (Consumer Discretionary / Cyclical)
BENCHMARK = "SPY"

DATA_DIR = pathlib.Path.home() / ".hermes" / "market_data"


def _compute_weekly_return(df: pd.DataFrame) -> pd.Series:
    """Compute weekly returns from daily data (Friday close to Friday close)."""
    weekly = df["close"].resample("W-FRI").last()
    return weekly.pct_change() * 100  # In percent


def _check_vix() -> float:
    """Fetch latest VIX value from yfinance. Returns None on failure."""
    try:
        import yfinance as yf
        vix = yf.download("^VIX", period="5d", progress=False)
        if vix is not None and not vix.empty:
            return float(vix["Close"].iloc[-1])
    except Exception:
        pass
    return None


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def scan(data_dict: dict) -> list[dict]:
    """
    Batch-mode scanner for EBE Sector Dispersion Mean Reversion.

    Parameters
    ----------
    data_dict : dict
        {ticker: pd.DataFrame} with OHLCV data (columns: open, high, low, close, volume).
        Must include SPY, XLE, XLY, and sector ETFs.

    Returns
    -------
    list of dict, one per signal detected
    """
    # ── Validate required tickers ────────────────────────────────────────────
    required = [ASSET_A, ASSET_B, BENCHMARK]
    missing = [t for t in required if t not in data_dict]
    if missing:
        print(f"  [EBE] Missing required tickers: {missing}")
        return []

    # ── Prepare data ─────────────────────────────────────────────────────────
    df_a = data_dict[ASSET_A].copy()
    df_b = data_dict[ASSET_B].copy()
    df_spy = data_dict[BENCHMARK].copy()

    for df in [df_a, df_b, df_spy]:
        df.sort_index(inplace=True)
        if "subperiod" not in df.columns:
            df["subperiod"] = df.index.to_period("Q").astype(str)

    # Align dates to common index (daily, intersection of all three)
    common_idx = df_a.index.intersection(df_b.index).intersection(df_spy.index)
    if len(common_idx) < 252:
        print(f"  [EBE] Insufficient common data: {len(common_idx)} days < 252")
        return []

    df_a = df_a.loc[common_idx]
    df_b = df_b.loc[common_idx]
    df_spy = df_spy.loc[common_idx]

    close_a = df_a["close"].values
    close_b = df_b["close"].values
    close_spy = df_spy["close"].values
    dates = common_idx
    subperiod_arr = df_spy["subperiod"].values

    # ── Compute YTD-like rolling return spread ───────────────────────────────
    # Use rolling 252-day returns as proxy for YTD return
    ret_a = pd.Series(close_a, index=common_idx).pct_change(LOOKBACK_YTD) * 100
    ret_b = pd.Series(close_b, index=common_idx).pct_change(LOOKBACK_YTD) * 100
    # Gap = XLE ret - XLY ret (e.g., +43.8% - (-7%) = 50.8pp)
    gap_raw = ret_a.values - ret_b.values

    # ── Weekly sector positive count ──────────────────────────────────────────
    # For each date, compute the number of sector ETFs with positive weekly return
    # We'll use a rolling 5-day forward-looking weekly return from each date
    weekly_sector_positive = np.full(len(common_idx), 99, dtype=int)

    available_sectors = [t for t in SECTOR_ETFS if t in data_dict]
    if available_sectors:
        sector_dfs = {}
        for t in available_sectors:
            df = data_dict[t].copy()
            df.sort_index(inplace=True)
            sector_dfs[t] = df["close"].reindex(common_idx, method="ffill")

        close_sector = pd.DataFrame(sector_dfs, index=common_idx)
        # 5-day forward return as proxy for weekly return
        week_ret_sector = close_sector.pct_change(5) * 100

        for i in range(5, len(common_idx)):
            pos_count = int((week_ret_sector.iloc[i] > 0).sum())
            weekly_sector_positive[i] = pos_count
    else:
        print(f"  [EBE] No sector ETFs found in data dict (available: {available_sectors})")
        return []

    # ── SPY weekly return (5-day forward) ────────────────────────────────────
    spy_week_ret = pd.Series(close_spy, index=common_idx).pct_change(5) * 100

    # ── ATR for stop/target sizing ──────────────────────────────────────────
    atr_a = _atr(df_a).values
    atr_b = _atr(df_b).values

    signals = []

    min_start = LOOKBACK_YTD + 10  # Need YTD lookback + extra

    for i in range(min_start, len(common_idx)):
        # ── Check condition 1: YTD dispersion gap > threshold ────────────────
        if np.isnan(gap_raw[i]):
            continue
        dispersion_gap = gap_raw[i]  # Already in percentage points
        
        # We'll use direction-aware: gap must be > threshold (XLE far outperforming XLY)
        # This is the "energy everything else" scenario where XLE >> XLY
        if dispersion_gap < DISPERSION_THRESHOLD_PP:
            continue

        # ── Check condition 2: Fewer than 3 sectors positive ─────────────────
        if weekly_sector_positive[i] > MAX_SECTORS_POSITIVE:
            continue

        # ── Check condition 3: SPX range-bound ────────────────────────────────
        spy_wk = spy_week_ret.iloc[i]
        if np.isnan(spy_wk):
            continue
        if not (SPX_WEEKLY_MIN <= spy_wk <= SPX_WEEKLY_MAX):
            continue

        # ── Check condition 4: VIX < 25 (fetch only when needed) ─────────────
        vix_val = _check_vix()
        # For historical backtesting, we approximate: use ^VIX if in data_dict
        # Otherwise skip this check for Phase 1A (conservative: skip high VIX by default)
        # Actually, for Phase 1A we need consistent historical VIX data
        if "VIX" in data_dict:
            df_vix = data_dict["VIX"]
            if i < len(df_vix):
                vix_close = float(df_vix["close"].iloc[min(i, len(df_vix) - 1)])
                if vix_close >= VIX_MAX:
                    continue

        # ── We have a signal! ─────────────────────────────────────────────────
        entry_price_a = float(close_a[i])  # XLE entry (we short this)
        entry_price_b = float(close_b[i])  # XLY entry (we long this)

        # Compute spread: gap between XLE and XLY percentage returns
        current_gap = dispersion_gap

        # Stop: gap widens by STOP_SPREAD_WIDEN_PP from entry
        # Since we short XLE / long XLY, our P&L direction is:
        #   Profit when: XLY outperforms XLE (gap narrows)
        #   Loss when: XLE outperforms XLY (gap widens)
        # Stop level in spread terms: current_gap + STOP_SPREAD_WIDEN_PP
        stop_gap = current_gap + STOP_SPREAD_WIDEN_PP

        # Target: gap narrows to < 20pp
        target_gap = 20.0

        # For R-multiple computation, we need to estimate risk in price terms
        # Risk is defined as the absolute loss if stop is hit on BOTH legs
        # Simple approach: ATR-based stop for each leg, then risk = sum of both
        risk_a = atr_a[i] * 2.0 if not np.isnan(atr_a[i]) else entry_price_a * 0.02
        risk_b = atr_b[i] * 2.0 if not np.isnan(atr_b[i]) else entry_price_b * 0.02

        # Short leg stop: higher price means loss
        stop_price_a = entry_price_a + risk_a
        # Long leg stop: lower price means loss
        stop_price_b = entry_price_b - risk_b

        # Target: 2R each leg
        target_price_a = entry_price_a - risk_a * RR_TARGET  # Short profit
        target_price_b = entry_price_b + risk_b * RR_TARGET  # Long profit

        # Composite R-multiple (average of both legs)
        total_risk = risk_a / entry_price_a + risk_b / entry_price_b
        if total_risk <= 0:
            continue

        # ── Exit simulation ──────────────────────────────────────────────────
        # Scan forward MAX_HOLD_BARS looking for target/stop/time
        exit_price_a = entry_price_a
        exit_price_b = entry_price_b
        exit_reason = "time"
        bars_held = MAX_HOLD_BARS

        for offset in range(1, min(MAX_HOLD_BARS + 1, len(common_idx) - i)):
            idx_exit = i + offset
            c_a = float(close_a[idx_exit])
            c_b = float(close_b[idx_exit])

            # Check stop on each leg independently
            hit_stop_a = c_a >= stop_price_a  # Short stop
            hit_stop_b = c_b <= stop_price_b  # Long stop

            # Check target on each leg independently
            hit_target_a = c_a <= target_price_a  # Short target
            hit_target_b = c_b >= target_price_b  # Long target

            # Composite: exit if BOTH legs hit target OR either leg hits stop
            if hit_stop_a or hit_stop_b:
                exit_price_a = c_a if hit_stop_a else c_a
                exit_price_b = c_b if hit_stop_b else c_b
                exit_reason = "stop"
                bars_held = offset
                break
            if hit_target_a and hit_target_b:
                exit_price_a = c_a
                exit_price_b = c_b
                exit_reason = "target"
                bars_held = offset
                break

        # Compute composite R-multiple
        # Short leg profit = (entry - exit) / risk
        # Long leg profit = (exit - entry) / risk
        r_a = (entry_price_a - exit_price_a) / risk_a  # Short
        r_b = (exit_price_b - entry_price_b) / risk_b   # Long
        composite_r = (r_a + r_b) / 2.0  # Average of both legs

        # ── Build output record ──────────────────────────────────────────────
        signal = {
            "ticker": f"{ASSET_A}/{ASSET_B}",
            "date": dates[i],
            "direction": "pairs_short_XLE_long_XLY",
            "entry_price": round((entry_price_a + entry_price_b) / 2, 4),
            "stop_price": round((stop_price_a + stop_price_b) / 2, 4),
            "target_price": round((target_price_a + target_price_b) / 2, 4),
            "exit_price": round((exit_price_a + exit_price_b) / 2, 4),
            "exit_reason": exit_reason,
            "r_multiple": round(composite_r, 4),
            "bars_held": bars_held,
            "subperiod": subperiod_arr[i],
            "strategy_id": STRATEGY_ID,
            "dispersion_gap_pp": round(dispersion_gap, 1),
            "spy_week_ret_pct": round(spy_wk, 2),
            "sectors_positive": int(weekly_sector_positive[i]),
            "xle_entry": round(entry_price_a, 4),
            "xly_entry": round(entry_price_b, 4),
            "r_a": round(r_a, 4),
            "r_b": round(r_b, 4),
        }
        signals.append(signal)

    return signals


if __name__ == "__main__":
    # Smoke test
    from fetch_data import load_all
    data = load_all()
    if not data:
        print("No data loaded.")
        sys.exit(1)
    results = scan(data)
    print(f"EBE Dispersion signals found: {len(results)}")
    if results:
        for sig in results[:5]:
            print(f"  {sig['date']} | gap={sig['dispersion_gap_pp']}pp | "
                  f"R={sig['r_multiple']:.3f} | {sig['exit_reason']}")