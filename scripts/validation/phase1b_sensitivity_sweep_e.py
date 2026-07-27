"""
phase1b_sensitivity_sweep_e.py — Phase 1B parameter sensitivity sweep for the
killed STR-E RSI Mean-Reversion strategy.

Does NOT touch scanner_e_rsi_mean_reversion.py or run_phase1a.py's existing
'e' registration. Standalone variant tester reusing the RSI/ATR/SMA indicator
math from the baseline scanner, run against the same cached universe.

Variants:
  V1  Long-only (drop short signal)
  V2  V1 + wider stop buffer (ATR mult 0.75 instead of 0.25)
  V3  V1 + V2 + longer hold (max_bars=14 instead of 8)
  V4  V1 + V2 + V3 + looser R:R filter (1.5 instead of 2.0)
"""

import sys
import datetime
import pathlib
import numpy as np
import pandas as pd

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))

from fetch_data import load_all  # noqa: E402

RSI_PERIOD = 14
ATR_PERIOD = 14
SMA_PERIOD = 20
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
LOOKBACK = 20

# --- Correct date-based subperiod classification (per task spec, verbatim) ---
SUBPERIODS = [
    ("period1_bull",    "2019-04-01", "2021-12-31"),
    ("period2_bear",    "2022-01-01", "2023-12-31"),
    ("period3_current", "2024-01-01", "2099-12-31"),
]


def label(date):
    d = date.date() if hasattr(date, "date") else pd.Timestamp(date).date()
    for name, start, end in SUBPERIODS:
        if datetime.date.fromisoformat(start) <= d <= datetime.date.fromisoformat(end):
            return name
    return "pre_warmup"


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _compute_atr(high, low, close, period=14):
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _compute_sma(close, period=20):
    return close.rolling(window=period).mean()


def _simulate_exit(closes, entry_idx, entry_price, stop_price, target_price, direction, max_bars):
    n = len(closes)
    for offset in range(1, max_bars + 1):
        idx = entry_idx + offset
        if idx >= n:
            last = min(entry_idx + offset - 1, n - 1)
            return closes[last], "time", offset
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
    exit_idx = min(entry_idx + max_bars, n - 1)
    return closes[exit_idx], "time", max_bars


def scan_variant(df: pd.DataFrame, ticker: str, *, long_only: bool,
                  atr_stop_mult: float, max_bars: int, min_rr: float,
                  rsi_oversold: int = RSI_OVERSOLD) -> list[dict]:
    df = df.copy()
    df.columns = df.columns.str.lower()
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(df.columns):
        raise ValueError(f"DataFrame missing columns: {required - set(df.columns)}")
    df.sort_index(inplace=True)

    close = df["close"]
    high = df["high"]
    low = df["low"]

    rsi = _compute_rsi(close, period=RSI_PERIOD)
    atr = _compute_atr(high, low, close, period=ATR_PERIOD)
    sma20 = _compute_sma(close, period=SMA_PERIOD)

    close_arr = close.values.astype(float)
    high_arr = high.values.astype(float)
    low_arr = low.values.astype(float)
    rsi_arr = rsi.values.astype(float)
    atr_arr = atr.values.astype(float)
    sma_arr = sma20.values.astype(float)
    dates = df.index

    signals = []
    min_start = max(RSI_PERIOD, ATR_PERIOD, SMA_PERIOD, LOOKBACK) + 1

    for i in range(min_start, len(df)):
        if (np.isnan(rsi_arr[i]) or np.isnan(rsi_arr[i - 1]) or
                np.isnan(atr_arr[i]) or np.isnan(sma_arr[i])):
            continue

        entry_price = close_arr[i]

        # LONG signal: RSI crosses up through rsi_oversold
        if rsi_arr[i - 1] < rsi_oversold and rsi_arr[i] >= rsi_oversold:
            stop_price = low_arr[i] - atr_stop_mult * atr_arr[i]
            risk = entry_price - stop_price
            if risk > 0:
                reward = max(2 * risk, abs(sma_arr[i] - entry_price))
                target_price = entry_price + reward
                rr = reward / risk
                if rr >= min_rr:
                    ep, er, bh = _simulate_exit(
                        close_arr, i, entry_price, stop_price, target_price, "long", max_bars
                    )
                    r_mult = (ep - entry_price) / risk
                    ts = pd.Timestamp(str(dates[i]))
                    signals.append({
                        "ticker": ticker, "date": ts.date(),
                        "direction": "long", "exit_reason": er,
                        "bars_held": bh, "r_multiple": round(r_mult, 4),
                        "subperiod": label(ts),
                    })

        if not long_only:
            if rsi_arr[i - 1] > RSI_OVERBOUGHT and rsi_arr[i] <= RSI_OVERBOUGHT:
                stop_price = high_arr[i] + atr_stop_mult * atr_arr[i]
                risk = stop_price - entry_price
                if risk <= 0:
                    continue
                reward = max(2 * risk, abs(sma_arr[i] - entry_price))
                target_price = entry_price - reward
                rr = reward / risk
                if rr < min_rr:
                    continue
                ep, er, bh = _simulate_exit(
                    close_arr, i, entry_price, stop_price, target_price, "short", max_bars
                )
                r_mult = (entry_price - ep) / risk
                ts = pd.Timestamp(str(dates[i]))
                signals.append({
                    "ticker": ticker, "date": ts.date(),
                    "direction": "short", "exit_reason": er,
                    "bars_held": bh, "r_multiple": round(r_mult, 4),
                    "subperiod": label(ts),
                })

    return signals


def summarize(all_signals: list[dict], name: str) -> dict:
    if not all_signals:
        return {"variant": name, "total_signals": 0, "signals_per_year": 0.0,
                 "avg_r": 0.0, "median_r": 0.0, "win_rate": 0.0,
                 "sub_positive": 0, "friction_flag": True, "classification": "❌ KILL"}
    res = pd.DataFrame(all_signals)
    res["date"] = pd.to_datetime(res["date"])
    years = max((res["date"].max() - res["date"].min()).days / 365.25, 0.1)
    signals_per_year = len(res) / years
    avg_r = float(res["r_multiple"].mean())
    median_r = float(res["r_multiple"].median())
    win_rate = float((res["r_multiple"] > 0).mean())

    sub_positive = 0
    for sp, _, _ in SUBPERIODS:
        sub = res[res["subperiod"] == sp]
        if len(sub) >= 3 and float(sub["r_multiple"].mean()) > 0:
            sub_positive += 1

    if signals_per_year < 12 or avg_r < 0.2:
        classification = "❌ KILL"
    elif signals_per_year >= 25 and avg_r >= 0.6 and sub_positive >= 2:
        classification = "✅ PASS"
    else:
        classification = "⚠️  WATCH"

    friction_flag = avg_r < 0.5

    return {
        "variant": name,
        "total_signals": len(res),
        "signals_per_year": round(signals_per_year, 1),
        "avg_r": round(avg_r, 4),
        "median_r": round(median_r, 4),
        "win_rate": round(win_rate, 4),
        "sub_positive": sub_positive,
        "friction_flag": friction_flag,
        "classification": classification,
    }


VARIANTS = {
    "V1_long_only": dict(long_only=True, atr_stop_mult=0.25, max_bars=8, min_rr=2.0),
    "V2_wider_stop": dict(long_only=True, atr_stop_mult=0.75, max_bars=8, min_rr=2.0),
    "V3_longer_hold": dict(long_only=True, atr_stop_mult=0.75, max_bars=14, min_rr=2.0),
    "V4_looser_rr": dict(long_only=True, atr_stop_mult=0.75, max_bars=14, min_rr=1.5),
    "V4b_deeper_oversold": dict(long_only=True, atr_stop_mult=0.75, max_bars=14, min_rr=2.0, rsi_oversold=25),
}


def main():
    print("Loading cached universe...")
    data = load_all()
    if not data:
        print("ERROR: no cached data found.")
        sys.exit(1)
    print(f"Loaded {len(data)} tickers.\n")

    all_summaries = []
    raw_frames = {}
    for name, params in VARIANTS.items():
        print(f"Running {name} ({params}) ...")
        sigs = []
        for ticker, df in data.items():
            try:
                sigs.extend(scan_variant(df, ticker, **params))
            except Exception as e:
                print(f"  ERROR on {ticker}: {e}")
        summary = summarize(sigs, name)
        all_summaries.append(summary)
        raw_frames[name] = sigs
        print(f"  -> {summary}\n")

    print("\n" + "=" * 100)
    print("PHASE 1B SENSITIVITY SWEEP — STR-E RSI Mean-Reversion")
    print("=" * 100)
    header = f"{'Variant':<18} {'Sig/Yr':>8} {'AvgR':>8} {'MedR':>8} {'WinR':>8} {'SubPos':>7} {'Friction':>9}  {'Status'}"
    print(header)
    print("-" * 100)
    for s in all_summaries:
        friction = "⚠️ FLAG" if s["friction_flag"] else "ok"
        print(f"{s['variant']:<18} {s['signals_per_year']:>8.1f} {s['avg_r']:>8.3f} {s['median_r']:>8.3f} "
              f"{s['win_rate']:>7.1%} {s['sub_positive']:>6}/3 {friction:>9}  {s['classification']}")

    return all_summaries, raw_frames


if __name__ == "__main__":
    main()
