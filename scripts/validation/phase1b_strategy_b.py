"""
phase1b_strategy_b.py — HermesForge Phase 1B (Strategy B)
Pre-registered perturbation tests for MACD Histogram Divergence strategy.

Pre-registered on: 2026-07-20
Based on Phase 1A findings:
  - Baseline: 79 sig/yr, avg R 0.565, win 43%, EV 0.565R
  - Key finding 1: Time-stop exits avg 2.83R (209/234 positive) — 8 bars too short
  - Key finding 2: Edge decaying across periods (1.07 → 0.42 → 0.15R)
  - Key finding 3: Shorts in bull market (period3) weak (0.09R, 37% win)
  - Key finding 4: Level 2 confirmation WORSE than Level 1 (0.14 vs 0.73R)
  - Key finding 5: Maturity 15-30 bars outperforms 50-100 bars
  - Key finding 6: 52.9% of trades hit stop (avg -2.0R) — stop may be too tight

THREE PRE-REGISTERED QUESTIONS (no others will be tested):
  Q1: Does a longer time stop (16 bars) improve EV vs 8 bars?
  Q2: Does direction filter (long-only in current bull, short-only in bear) fix edge decay?
  Q3: Does tightening maturity to 15-40 bars (exclude extended trends) improve quality?
"""

import sys
import pathlib
import pandas as pd
import numpy as np

REPO = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "validation"))

from fetch_data import load_all
from scanners.scanner_b_macd_divergence import (
    _compute_macd, _compute_rsi, _compute_atr,
    _count_consecutive_above_zero, _count_consecutive_below_zero,
    _histogram_narrowing_count, _simulate_exit,
    NARROWING_BARS, SWING_LOOKBACK, MIN_RR, ATR_STOP_MULT, TARGET_LOOKBACK
)

RESULTS_DIR = REPO / "scripts" / "validation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

SUBPERIODS = {
    "period1_bull":    ("2019-04-01", "2021-12-31"),
    "period2_bear":    ("2022-01-01", "2023-12-31"),
    "period3_current": ("2024-01-01", "2099-12-31"),
}

def label_subperiod(date):
    import datetime
    d = pd.Timestamp(date).date()
    if d is None:
        return "pre_warmup"
    for name, (start, end) in SUBPERIODS.items():
        if datetime.date.fromisoformat(start) <= d <= datetime.date.fromisoformat(end):
            return name
    return "pre_warmup"


def run_scanner_variant(
    data: dict,
    variant_id: str,
    time_stop_bars: int = 8,
    max_maturity_bars: int = 999,
    direction_filter: str = "both",   # "both" | "long_only" | "short_only" | "regime_aware"
) -> pd.DataFrame:
    """
    Run Strategy B scanner with modified parameters.
    direction_filter='regime_aware' = long only in period3, short+long in period1/2.
    """
    all_signals = []

    for ticker, df in data.items():
        close = df["close"].values
        high  = df["high"].values
        low   = df["low"].values
        dates = df.index
        subperiod_arr = [label_subperiod(d) for d in dates]

        macd_s, signal_s, hist_s = _compute_macd(df["close"])
        macd_arr   = macd_s.values
        signal_arr = signal_s.values
        hist_arr   = hist_s.values
        rsi_arr    = _compute_rsi(df["close"]).values
        atr_s      = _compute_atr(df["high"], df["low"], df["close"])
        atr_arr    = atr_s.values

        min_idx = 60
        for i in range(min_idx, len(close)):
            sp = subperiod_arr[i]

            for direction in ["bearish", "bullish"]:
                # Direction filter
                if direction_filter == "long_only" and direction == "bearish":
                    continue
                if direction_filter == "short_only" and direction == "bullish":
                    continue
                if direction_filter == "regime_aware":
                    # In current bull (period3): only take long (bullish) signals
                    if sp == "period3_current" and direction == "bearish":
                        continue

                # Maturity gate
                if direction == "bearish":
                    mb = _count_consecutive_above_zero(macd_arr, i - 1)
                else:
                    mb = _count_consecutive_below_zero(macd_arr, i - 1)

                if mb < 15 or mb > max_maturity_bars:
                    continue

                # Stage 1
                if direction == "bearish":
                    window = high[max(0, i - SWING_LOOKBACK): i + 1]
                    near_extreme = high[i] >= np.max(window) * 0.99
                    nc = _histogram_narrowing_count(hist_arr, i, "bearish")
                else:
                    window = low[max(0, i - SWING_LOOKBACK): i + 1]
                    near_extreme = low[i] <= np.min(window) * 1.01
                    nc = _histogram_narrowing_count(hist_arr, i, "bullish")

                if not near_extreme or nc < NARROWING_BARS:
                    continue

                # Stage 2
                prior_start = i - 60
                prior_end   = i - 5
                if prior_start < 0:
                    continue

                if direction == "bearish":
                    ph = high[prior_start: prior_end + 1]
                    pb = prior_start + int(np.argmax(ph))
                    if macd_arr[i] >= macd_arr[pb]:
                        continue
                else:
                    pl = low[prior_start: prior_end + 1]
                    pb = prior_start + int(np.argmin(pl))
                    if macd_arr[i] <= macd_arr[pb]:
                        continue

                # Entry trigger (within +2 bars)
                crossover = False
                for offset in range(0, 3):
                    j = i + offset
                    if j <= 0 or j >= len(macd_arr):
                        break
                    if direction == "bearish":
                        if macd_arr[j] < signal_arr[j] and macd_arr[j-1] >= signal_arr[j-1]:
                            crossover = True; break
                    else:
                        if macd_arr[j] > signal_arr[j] and macd_arr[j-1] <= signal_arr[j-1]:
                            crossover = True; break
                if not crossover:
                    continue

                # Stop and target
                atr_val = float(atr_arr[i]) if not np.isnan(atr_arr[i]) else 0.0
                if atr_val <= 0:
                    continue

                if direction == "bearish":
                    entry_price  = float(close[i])
                    stop_price   = entry_price + ATR_STOP_MULT * atr_val
                    target_price = float(np.min(low[max(0, i - TARGET_LOOKBACK): i]))
                    if target_price >= entry_price:
                        continue
                    risk = stop_price - entry_price
                else:
                    entry_price  = float(close[i])
                    stop_price   = entry_price - ATR_STOP_MULT * atr_val
                    target_price = float(np.max(high[max(0, i - TARGET_LOOKBACK): i]))
                    if target_price <= entry_price:
                        continue
                    risk = entry_price - stop_price

                if risk <= 0:
                    continue

                rr = abs(target_price - entry_price) / risk
                if rr < MIN_RR:
                    continue

                # Confirmation level
                if direction == "bearish":
                    conf = "Level 2" if rsi_arr[i] >= 70 else "Level 1"
                else:
                    conf = "Level 2" if rsi_arr[i] <= 30 else "Level 1"

                # Exit simulation with MODIFIED time stop
                ep, er, bh = _simulate_exit(
                    close, i, entry_price, stop_price, target_price,
                    "short" if direction == "bearish" else "long",
                    max_bars=time_stop_bars
                )

                # Realised R
                if direction == "bearish":
                    realised_r = (entry_price - ep) / risk
                else:
                    realised_r = (ep - entry_price) / risk

                all_signals.append({
                    "ticker":             ticker,
                    "date":               str(dates[i])[:10],
                    "direction":          "short" if direction == "bearish" else "long",
                    "entry_price":        round(entry_price, 4),
                    "stop_price":         round(stop_price, 4),
                    "target_price":       round(target_price, 4),
                    "exit_price":         round(ep, 4),
                    "exit_reason":        er,
                    "r_multiple":         round(realised_r, 4),
                    "bars_held":          bh,
                    "subperiod":          sp,
                    "confirmation_level": conf,
                    "macd_bars_above_zero": mb,
                    "variant":            variant_id,
                    "time_stop_bars":     time_stop_bars,
                    "max_maturity_bars":  max_maturity_bars,
                    "direction_filter":   direction_filter,
                })

    return pd.DataFrame(all_signals)


def summarize(df: pd.DataFrame, variant_id: str) -> dict:
    if df.empty:
        return {"variant": variant_id, "n": 0, "sig_yr": 0, "avg_r": 0,
                "median_r": 0, "win_rate": 0, "ev": 0}
    df["date"] = pd.to_datetime(df["date"])
    years = max((df["date"].max() - df["date"].min()).days / 365.25, 0.1)
    wins  = df[df["r_multiple"] > 0]["r_multiple"]
    losses= df[df["r_multiple"] <= 0]["r_multiple"]
    w_mean = float(wins.mean()) if len(wins) else 0.0   # type: ignore[arg-type]
    l_mean = float(losses.mean()) if len(losses) else 0.0  # type: ignore[arg-type]
    ev = w_mean * len(wins)/len(df) + l_mean * len(losses)/len(df)
    return {
        "variant":   variant_id,
        "n":         len(df),
        "sig_yr":    round(len(df)/years, 1),
        "avg_r":     round(float(df["r_multiple"].mean()), 3),    # type: ignore[arg-type]
        "median_r":  round(float(df["r_multiple"].median()), 3),  # type: ignore[arg-type]
        "win_rate":  round(float((df["r_multiple"] > 0).mean()), 3),  # type: ignore[arg-type]
        "ev":        round(ev, 3),
        "avg_win":   round(w_mean, 2),
        "avg_loss":  round(l_mean, 2),
    }


def print_comparison(summaries: list[dict]):
    header = f"{'Variant':<30} {'N':>5} {'Sig/Yr':>7} {'Avg R':>7} {'Median':>7} {'Win%':>7} {'EV':>7} {'AvgWin':>8} {'AvgLoss':>8}"
    print(header)
    print("-" * len(header))
    for s in summaries:
        print(f"{s['variant']:<30} {s['n']:>5} {s['sig_yr']:>7.1f} {s['avg_r']:>7.3f} "
              f"{s['median_r']:>7.3f} {s['win_rate']:>7.1%} {s['ev']:>7.3f} "
              f"{s['avg_win']:>8.2f} {s['avg_loss']:>8.2f}")


def main():
    print("Loading data...")
    data = load_all()
    print(f"Loaded {len(data)} tickers\n")

    # ── BASELINE (replicate Phase 1A) ───────────────────────────────────
    print("Running variants...")
    variants = {}

    variants["baseline_8bar"] = run_scanner_variant(
        data, "baseline_8bar", time_stop_bars=8)

    # ── Q1: TIME STOP LENGTH ────────────────────────────────────────────
    # Phase 1A finding: time-stop exits avg 2.83R with 209/234 positive
    # Hypothesis: longer hold allows more winners to reach target
    variants["time_stop_12"] = run_scanner_variant(
        data, "time_stop_12", time_stop_bars=12)
    variants["time_stop_16"] = run_scanner_variant(
        data, "time_stop_16", time_stop_bars=16)
    variants["time_stop_24"] = run_scanner_variant(
        data, "time_stop_24", time_stop_bars=24)

    # ── Q2: DIRECTION FILTER (regime-aware) ─────────────────────────────
    # Phase 1A finding: shorts in period3 (current bull) avg 0.09R 37% win
    # Hypothesis: filtering longs-only in bull regime improves edge
    variants["regime_aware"] = run_scanner_variant(
        data, "regime_aware", direction_filter="regime_aware")
    variants["short_only"] = run_scanner_variant(
        data, "short_only", direction_filter="short_only")
    variants["long_only"] = run_scanner_variant(
        data, "long_only", direction_filter="long_only")

    # ── Q3: MATURITY CAP ────────────────────────────────────────────────
    # Phase 1A finding: 50-100 bar maturity bucket underperforms (0.24R)
    # Hypothesis: capping maturity at 40 bars filters over-extended trends
    variants["maturity_cap_40"] = run_scanner_variant(
        data, "maturity_cap_40", max_maturity_bars=40)
    variants["maturity_cap_30"] = run_scanner_variant(
        data, "maturity_cap_30", max_maturity_bars=30)

    # ── COMBINED: best from each Q ──────────────────────────────────────
    variants["combined_best"] = run_scanner_variant(
        data, "combined_best",
        time_stop_bars=16,
        direction_filter="regime_aware",
        max_maturity_bars=40,
    )

    # Save all results
    all_dfs = []
    for vid, df in variants.items():
        if not df.empty:
            df.to_csv(RESULTS_DIR / f"STR-B-phase1b-{vid}.csv", index=False)
            all_dfs.append(df)

    # Print comparison
    print(f"\n{'='*90}")
    print("PHASE 1B RESULTS — STRATEGY B PERTURBATIONS")
    print(f"{'='*90}")
    summaries = [summarize(df, vid) for vid, df in variants.items()]
    print_comparison(summaries)

    # Sub-period breakdown for best variants
    print(f"\n{'='*90}")
    print("SUB-PERIOD BREAKDOWN — Key Variants")
    print(f"{'='*90}")
    key_variants = ["baseline_8bar", "time_stop_16", "regime_aware", "combined_best"]
    for vid in key_variants:
        df = variants[vid]
        if df.empty:
            continue
        print(f"\n{vid}:")
        for sp, label in [("period1_bull","2019-21"), ("period2_bear","2022-23"), ("period3_current","2024+")]:
            sub = df[df["subperiod"]==sp]
            if len(sub) == 0:
                print(f"  {label}: no data")
                continue
            avg_r = float(sub["r_multiple"].mean())
            wr    = float((sub["r_multiple"] > 0).mean())
            print(f"  {label}: n={len(sub)}, avg_R={avg_r:.3f}, win%={wr:.1%}")

    # Save summary report
    report_lines = [
        "# Phase 1B Results — Strategy B",
        "",
        "## Pre-Registered Questions",
        "- Q1: Does longer time stop (16 bars) improve EV?",
        "- Q2: Does regime-aware direction filter fix edge decay?",
        "- Q3: Does capping maturity at 40 bars improve quality?",
        "",
        "## Results Table",
        "",
        f"| {'Variant':<30} | {'N':>5} | {'Sig/Yr':>7} | {'Avg R':>7} | {'Win%':>7} | {'EV':>7} |",
        f"|{'-'*32}|{'-'*7}|{'-'*9}|{'-'*9}|{'-'*9}|{'-'*9}|",
    ]
    for s in summaries:
        report_lines.append(
            f"| {s['variant']:<30} | {s['n']:>5} | {s['sig_yr']:>7.1f} | "
            f"{s['avg_r']:>7.3f} | {s['win_rate']:>7.1%} | {s['ev']:>7.3f} |"
        )

    report_path = RESULTS_DIR / "phase1b-strategy-b-report.md"
    report_path.write_text("\n".join(report_lines))
    print(f"\nReport saved → {report_path}")


if __name__ == "__main__":
    main()
