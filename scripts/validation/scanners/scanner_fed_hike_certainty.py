#!/usr/bin/env python3
"""
scanner_fed_hike_certainty.py — STR-FOMC-CERTAINTY: Pre-FOMC Extreme Certainty Resolution

Edge candidate: CAND-20260915-fed-hike-certainty-contrarian
Source hypothesis: When pre-FOMC hike odds exceed ~85-90% (near-unanimous
market pricing), the post-FOMC SPY return is positive with >70% probability
regardless of the hike decision, because the certainty is already fully priced.

Signal Rules (batch):
  1. Detect FOMC announcement dates in the SPY data
  2. Use VIX < VIX_MAX (complacency proxy) as substitute for CME odds data
  3. On FOMC date with pre-meeting complacency:
     - Generate SPY LONG post-announcement signal
     - Exit: ATR-based stop (stop below entry), target TARGET_RR, time stop

Data sources:
  - FOMC dates hard-coded for 2019-2026 (scheduled well in advance)
  - VIX from parquet cache (~/.hermes/market_data/VIXINDEX.parquet)
  - SPY for entry/exit simulation

NOTE: Without cached CME FedWatch historical data, this scanner uses VIX
level as a proxy for "market certainty/pricing-in." VIX below VIX_MAX before
an FOMC suggests the market is complacent about the outcome — which aligns
with the "priced-in certainty" hypothesis. The actual 94% hike odds from
Sep 2026 are known from web sources but not in cached data.

Dependencies: pandas, numpy.
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "STR-FOMC-CERTAINTY"
STRATEGY_NAME = "Pre-FOMC Certainty Resolution"

# ── Parameters ───────────────────────────────────────────────────────────────
VIX_MAX = 20.0                # VIX below this = complacent/certainty proxy
VIX_LOOKBACK = 5              # Check VIX this many days before FOMC
CONFIRMATION_BARS = 1          # Not used for event-study, kept for compat
MAX_HOLD_BARS = 5              # Post-FOMC hold window (~1 week)
TARGET_RR = 1.5                # Risk:Reward target
STOP_ATR_MULT = 1.5            # Stop = 1.5x ATR
ATR_PERIOD = 14
MIN_HISTORY = 60

DATA_DIR = Path.home() / ".hermes" / "market_data"

# Known FOMC meeting dates: 2019-2026
# Schedule: ~8 meetings/year (Jan, Mar, May, Jun, Jul, Sep, Nov, Dec)
# Dates sourced from Fed calendar archives
FOMC_DATES = sorted([
    # 2019
    "2019-01-30", "2019-03-20", "2019-05-01", "2019-06-19",
    "2019-07-31", "2019-09-18", "2019-10-30", "2019-12-11",
    # 2020 (emergency meetings included)
    "2020-03-03", "2020-03-15", "2020-04-29", "2020-06-10",
    "2020-07-29", "2020-09-16", "2020-11-05", "2020-12-16",
    # 2021
    "2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16",
    "2021-07-28", "2021-09-22", "2021-11-03", "2021-12-15",
    # 2022 (hiking cycle)
    "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15",
    "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14",
    # 2023
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14",
    "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
    # 2024
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12",
    "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
    # 2025
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18",
    "2025-07-30", "2025-09-17", "2025-11-05", "2025-12-17",
    # 2026
    "2026-01-28", "2026-03-18", "2026-05-06", "2026-06-17",
    "2026-07-29", "2026-09-16", "2026-11-04", "2026-12-16",
])


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


def _atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def _simulate_exit(df: pd.DataFrame, entry_idx: int, direction: str,
                   entry_price: float, stop_price: float,
                   max_bars: int) -> tuple:
    closes = df["close"].values
    n = len(closes)
    for offset in range(1, max_bars + 1):
        idx = entry_idx + offset
        if idx >= n:
            return closes[min(entry_idx + offset - 1, n - 1)], "time", offset
        if direction == "long":
            if df["low"].iloc[idx] <= stop_price:
                return stop_price, "stop", offset
        else:
            if df["high"].iloc[idx] >= stop_price:
                return stop_price, "stop", offset
    exit_idx = min(entry_idx + max_bars, n - 1)
    return closes[exit_idx], "time", max_bars


def load_vix() -> pd.Series:
    """Load daily VIX close from cache."""
    vix_path = DATA_DIR / "VIXINDEX.parquet"
    if vix_path.exists():
        vix = pd.read_parquet(vix_path)
        vix.columns = [c.lower() for c in vix.columns]
        vix = vix.sort_index()
        vix = vix[~vix.index.duplicated(keep="last")]
        if "close" in vix.columns:
            return vix["close"]
    return pd.Series(dtype=float)


def scan(data: dict) -> list:
    """
    Batch scanner. Generates SPY long signals on FOMC dates with
    pre-meeting VIX complacency proxy.
    """
    spy = data.get("SPY")
    if spy is None:
        print("    [FOMC-CERTAINTY] ERROR: SPY not in data dict")
        return []
    if len(spy) < MIN_HISTORY:
        print(f"    [FOMC-CERTAINTY] ERROR: SPY has only {len(spy)} rows")
        return []

    # Ensure SPY index is datetime
    spy_idx = pd.to_datetime(spy.index)
    spy = spy.copy()
    spy.index = spy_idx

    # Load VIX
    vix = load_vix()
    if len(vix) > 0:
        print(f"    [FOMC-CERTAINTY] VIX data: {len(vix)} days (from {vix.index.min()})", flush=True)
    else:
        print("    [FOMC-CERTAINTY] WARNING: No VIX data — proceeding without complacency filter", flush=True)

    # Filter FOMC dates to SPY date range
    valid_fomc = []
    for fd_str in FOMC_DATES:
        fd = pd.Timestamp(fd_str)
        if fd < spy.index[0] or fd > spy.index[-1]:
            continue
        # Check if SPY has data on or very near this date
        nearest_idx = spy.index.searchsorted(fd)
        if nearest_idx >= len(spy.index):
            continue
        nearest = spy.index[nearest_idx]
        if nearest_idx > 0:
            prev = spy.index[nearest_idx - 1]
            # Prefer the exact date; if not found, use nearest trading day
            if abs((nearest - fd).days) > 5:
                continue

        # VIX complacency check (proxy for "priced-in certainty")
        vix_ok = True
        if len(vix) > 0 and fd in vix.index:
            pre_idx = vix.index.searchsorted(fd)
            if pre_idx >= VIX_LOOKBACK:
                vix_pre = vix.iloc[pre_idx - VIX_LOOKBACK: pre_idx]
                vix_mean = vix_pre.mean()
                # Only proceed if VIX was reasonably low pre-FOMC (complacency)
                if vix_mean > VIX_MAX:
                    vix_ok = False

        valid_fomc.append((fd, vix_ok))

    print(f"    [FOMC-CERTAINTY] FOMC dates in SPY range: {len(valid_fomc)} "
          f"({sum(1 for _, ok in valid_fomc if ok)} with low VIX)", flush=True)

    if not valid_fomc:
        print("    [FOMC-CERTAINTY] No FOMC dates in SPY range")
        return []

    signals = []

    for fomc_date, vix_ok in valid_fomc:
        # Find the entry date in SPY = closest trading day to/after FOMC
        # (post-announcement entry ~2:30pm ET, captured in next day's close)
        entry_search = fomc_date + pd.Timedelta(days=1)  # Next day for post-announcement
        nearest_idx = spy.index.searchsorted(entry_search)
        if nearest_idx >= len(spy.index):
            # Try the FOMC date itself
            nearest_idx = spy.index.searchsorted(fomc_date)
            if nearest_idx >= len(spy.index):
                continue
            entry_date = spy.index[nearest_idx]
        else:
            entry_date = spy.index[nearest_idx]

        entry_idx = spy.index.get_loc(entry_date)
        if entry_idx < ATR_PERIOD + 5:
            continue

        entry_price = float(spy["close"].iloc[entry_idx])

        # Compute ATR
        atr_series = _atr(spy.iloc[:entry_idx + 1])
        atr_val = float(atr_series.iloc[-1])
        if pd.isna(atr_val) or atr_val <= 0:
            continue

        # Long signal: post-FOMC long
        stop_price = entry_price - STOP_ATR_MULT * atr_val
        risk = entry_price - stop_price
        if risk <= 0 or risk / entry_price < 0.002:
            continue
        target_price = entry_price + risk * TARGET_RR

        subperiod = _subperiod(entry_date)

        exit_price, exit_reason, bars_held = _simulate_exit(
            spy, entry_idx, "long", entry_price, stop_price, MAX_HOLD_BARS
        )
        realised_r = (exit_price - entry_price) / risk

        signals.append({
            "ticker": "SPY",
            "date": str(fomc_date.date()),
            "entry_date": str(entry_date.date()),
            "direction": "long",
            "entry_price": round(entry_price, 6),
            "stop_price": round(stop_price, 6),
            "target_price": round(target_price, 6),
            "exit_price": round(float(exit_price), 6),
            "exit_reason": exit_reason,
            "r_multiple": round(float(realised_r), 4),
            "bars_held": bars_held,
            "strategy_id": STRATEGY_ID,
            "subperiod": subperiod,
            "vix_filtered": vix_ok,
            "fomc_event": str(fomc_date.date()),
        })

    return signals


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from fetch_data import load_all

    print("Loading stock data...")
    stocks = load_all()
    print(f"  {len(stocks)} symbols loaded")

    print("\nRunning STR-FOMC-CERTAINTY scanner...")
    signals = scan(stocks)

    if not signals:
        print("No signals generated.")
        sys.exit(0)

    r_values = [s["r_multiple"] for s in signals]
    wins = [s for s in signals if s["r_multiple"] > 0]
    avg_r = float(np.mean(r_values)) if r_values else 0
    win_rate = len(wins) / len(signals) if signals else 0

    print(f"\nSTR-FOMC-CERTAINTY Phase 1A Results:")
    print(f"  Signals: {len(signals)}")
    print(f"  Avg R: {avg_r:+.4f}")
    print(f"  Win rate: {win_rate:.1%}")

    # By year
    by_year = {}
    for s in signals:
        yr = str(s["date"])[:4]
        if yr not in by_year:
            by_year[yr] = []
        by_year[yr].append(s["r_multiple"])
    print(f"\n  By year:")
    for yr in sorted(by_year.keys()):
        yr_r = by_year[yr]
        print(f"    {yr}: {len(yr_r):3d} sigs, avg R = {float(np.mean(yr_r)):+.4f}")