"""
phase1b_bollinger_sweep.py — Phase 1B parameter sensitivity sweep for the
killed STR-F Bollinger Squeeze Breakout strategy.

Reuses the Bollinger Band math / exit-simulation pattern from
scanners/scanner_f_bollinger_squeeze.py but parameterizes:
  - long_only          : drop the short/lower-band-break signal
  - rr_target          : reward:risk multiple used for the profit target
  - max_hold           : time-stop bar count
  - volume_mult        : volume confirmation multiplier
  - squeeze_window     : trailing bars used for squeeze-low detection

Runs each variant against the SAME cached universe used by run_phase1a.py
(~/.hermes/market_data/*.parquet, loaded via fetch_data.load_all()), and
classifies each variant per ADR-004 using the CORRECT date-based sub-period
buckets (NOT the CSV's quarter-label 'subperiod' column, which is a known
bug in the original scanner build).

Does NOT touch scanner_f_bollinger_squeeze.py or run_phase1a.py's existing
'f' registration — this is a standalone Phase 1B exploration script.
"""

import datetime
import pathlib
import sys

import numpy as np
import pandas as pd

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from fetch_data import load_all  # noqa: E402

# --------------------------------------------------------------------------- #
# Correct date-based sub-period bucketing (per ADR-004 / task spec)          #
# --------------------------------------------------------------------------- #
SUBPERIODS = [
    ("period1_bull",    "2019-04-01", "2021-12-31"),
    ("period2_bear",    "2022-01-01", "2023-12-31"),
    ("period3_current", "2024-01-01", "2099-12-31"),
]


def label(date) -> str:
    d = pd.Timestamp(date).date()
    for name, start, end in SUBPERIODS:
        if datetime.date.fromisoformat(start) <= d <= datetime.date.fromisoformat(end):
            return name
    return "pre_warmup"


# ADR-004 thresholds
KILL_SIGNALS_PER_YEAR = 12
KILL_AVG_R = 0.2
WATCH_SIGNALS_PER_YEAR = 25
PASS_AVG_R = 0.6
FRICTION_FLAG_R = 0.5


def classify(signals_per_year: float, avg_r: float, sub_positive: int) -> str:
    if signals_per_year < KILL_SIGNALS_PER_YEAR or avg_r < KILL_AVG_R:
        return "KILL"
    if signals_per_year >= WATCH_SIGNALS_PER_YEAR and avg_r >= PASS_AVG_R and sub_positive >= 2:
        return "PASS"
    return "WATCH"


# --------------------------------------------------------------------------- #
# Parameterized scanner core (adapted from scanner_f_bollinger_squeeze.py)   #
# --------------------------------------------------------------------------- #
BB_PERIOD = 20
BB_STD_MULT = 2.0
LOOKBACK = 60


def simulate_exit(df, entry_idx, entry_price, stop_price, target_price, direction, max_hold):
    if direction == "long":
        risk = entry_price - stop_price
    else:
        risk = stop_price - entry_price

    n = len(df)
    close = df["close"]

    for offset in range(1, max_hold + 1):
        bar_idx = entry_idx + offset
        if bar_idx >= n:
            last_close = close.iloc[bar_idx - 1] if bar_idx > 0 else entry_price
            if direction == "long":
                r_mult = (last_close - entry_price) / risk
            else:
                r_mult = (entry_price - last_close) / risk
            return dict(exit_reason="time", bars_held=offset, r_multiple=round(float(r_mult), 3))

        c = close.iloc[bar_idx]
        if direction == "long":
            if c <= stop_price:
                r_mult = (c - entry_price) / risk
                return dict(exit_reason="stop", bars_held=offset, r_multiple=round(float(r_mult), 3))
            if c >= target_price:
                r_mult = (c - entry_price) / risk
                return dict(exit_reason="target", bars_held=offset, r_multiple=round(float(r_mult), 3))
        else:
            if c >= stop_price:
                r_mult = (entry_price - c) / risk
                return dict(exit_reason="stop", bars_held=offset, r_multiple=round(float(r_mult), 3))
            if c <= target_price:
                r_mult = (entry_price - c) / risk
                return dict(exit_reason="target", bars_held=offset, r_multiple=round(float(r_mult), 3))

    last_close = close.iloc[entry_idx + max_hold]
    if direction == "long":
        r_mult = (last_close - entry_price) / risk
    else:
        r_mult = (entry_price - last_close) / risk
    return dict(exit_reason="time", bars_held=max_hold, r_multiple=round(float(r_mult), 3))


def scan_variant(
    df: pd.DataFrame,
    ticker: str,
    strategy_id: str,
    long_only: bool = False,
    rr_target: float = 2.0,
    max_hold: int = 10,
    volume_mult: float = 1.2,
    squeeze_window: int = 60,
) -> list[dict]:
    df = df.copy()
    df.columns = df.columns.str.lower()
    df.sort_index(inplace=True)

    close = df["close"]
    volume = df["volume"]

    sma = close.rolling(window=BB_PERIOD).mean()
    std = close.rolling(window=BB_PERIOD).std(ddof=0)
    upper_band = sma + BB_STD_MULT * std
    lower_band = sma - BB_STD_MULT * std
    band_width = (upper_band - lower_band) / sma

    squeeze_min = band_width.rolling(window=squeeze_window).min()
    is_squeeze = band_width == squeeze_min

    avg_volume = volume.rolling(window=BB_PERIOD).mean()

    lookback = max(LOOKBACK, squeeze_window)
    signals = []

    for i in range(lookback, len(df)):
        if i - 1 < 0:
            continue
        squeeze_yesterday = is_squeeze.iloc[i - 1]
        if pd.isna(squeeze_yesterday) or not bool(squeeze_yesterday):
            continue

        upper_yesterday = upper_band.iloc[i - 1]
        lower_yesterday = lower_band.iloc[i - 1]
        if pd.isna(upper_yesterday) or pd.isna(lower_yesterday):
            continue

        today_close = close.iloc[i]
        today_volume = volume.iloc[i]
        avg_vol_i = avg_volume.iloc[i]
        if pd.isna(avg_vol_i) or avg_vol_i <= 0:
            continue

        volume_ratio = today_volume / avg_vol_i
        if volume_ratio < volume_mult:
            continue

        direction = None
        if today_close > upper_yesterday:
            direction = "long"
        elif (not long_only) and today_close < lower_yesterday:
            direction = "short"
        else:
            continue

        today_upper = upper_band.iloc[i]
        today_lower = lower_band.iloc[i]
        if pd.isna(today_upper) or pd.isna(today_lower):
            continue

        entry_price = float(today_close)

        if direction == "long":
            stop_price = float(today_lower)
            if stop_price >= entry_price:
                continue
            risk = entry_price - stop_price
            target_price = entry_price + rr_target * risk
        else:
            stop_price = float(today_upper)
            if stop_price <= entry_price:
                continue
            risk = stop_price - entry_price
            target_price = entry_price - rr_target * risk

        if risk <= 0:
            continue

        reward = abs(target_price - entry_price)
        rr = reward / risk
        if rr < rr_target:
            continue

        exit_info = simulate_exit(df, i, entry_price, stop_price, target_price, direction, max_hold)

        raw_date = df.index[i]
        ts = pd.Timestamp(str(raw_date))

        signals.append(dict(
            ticker=ticker,
            date=ts.date(),
            direction=direction,
            strategy_id=strategy_id,
            **exit_info,
        ))

    return signals


def summarize(results: pd.DataFrame, name: str) -> dict:
    if results.empty:
        return dict(variant=name, total=0, sig_per_yr=0.0, avg_r=0.0, median_r=0.0,
                    win_rate=0.0, sub_positive=0, friction=True, classification="KILL")

    results = results.copy()
    results["date"] = pd.to_datetime(results["date"])
    years = max((results["date"].max() - results["date"].min()).days / 365.25, 0.1)
    sig_per_yr = len(results) / years
    avg_r = float(results["r_multiple"].mean())
    median_r = float(results["r_multiple"].median())
    win_rate = float((results["r_multiple"] > 0).mean())

    results["sp"] = results["date"].apply(label)
    sub_positive = 0
    for sp in ["period1_bull", "period2_bear", "period3_current"]:
        sub = results[results["sp"] == sp]
        if len(sub) >= 3 and float(sub["r_multiple"].mean()) > 0:
            sub_positive += 1

    classification = classify(sig_per_yr, avg_r, sub_positive)
    friction = avg_r < FRICTION_FLAG_R

    return dict(
        variant=name,
        total=len(results),
        sig_per_yr=round(sig_per_yr, 1),
        avg_r=round(avg_r, 3),
        median_r=round(median_r, 3),
        win_rate=round(win_rate, 3),
        sub_positive=sub_positive,
        friction=friction,
        classification=classification,
    )


VARIANTS = {
    "V1_long_only": dict(long_only=True, rr_target=2.0, max_hold=10, volume_mult=1.2, squeeze_window=60),
    "V2_long_only_rr1.2": dict(long_only=True, rr_target=1.2, max_hold=10, volume_mult=1.2, squeeze_window=60),
    "V3_long_only_rr1.2_hold20": dict(long_only=True, rr_target=1.2, max_hold=20, volume_mult=1.2, squeeze_window=60),
    "V4_long_only_rr1.2_hold20_vol1.0": dict(long_only=True, rr_target=1.2, max_hold=20, volume_mult=1.0, squeeze_window=60),
}


def main():
    print("Loading cached data...")
    data = load_all()
    print(f"Loaded {len(data)} tickers.\n")

    all_summaries = []
    for name, params in VARIANTS.items():
        print(f"Running {name} -> {params}")
        all_signals = []
        for ticker, df in data.items():
            try:
                sigs = scan_variant(df, ticker, strategy_id=f"F2-{name}", **params)
                all_signals.extend(sigs)
            except Exception as e:
                print(f"  ERROR {ticker}: {e}")
        results = pd.DataFrame(all_signals)
        summary = summarize(results, name)
        all_summaries.append(summary)
        print(f"  -> {summary}\n")

    print("=" * 110)
    print("PHASE 1B SENSITIVITY SWEEP — STR-F Bollinger Squeeze Breakout")
    print("=" * 110)
    header = f"{'Variant':<35}{'Sig/Yr':>8}{'AvgR':>8}{'MedR':>8}{'WinR':>8}{'SubPos':>8}{'Friction':>10}{'Class':>8}"
    print(header)
    print("-" * 110)
    for s in all_summaries:
        print(
            f"{s['variant']:<35}{s['sig_per_yr']:>8.1f}{s['avg_r']:>8.3f}{s['median_r']:>8.3f}"
            f"{s['win_rate']:>8.1%}{s['sub_positive']:>7}/3{('YES' if s['friction'] else 'no'):>10}{s['classification']:>8}"
        )

    return all_summaries


if __name__ == "__main__":
    main()
