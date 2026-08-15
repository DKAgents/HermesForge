#!/usr/bin/env python3
"""
run_phase1b_q.py — HermesForge Phase 1B Walk-Forward Validation for STR-Q
=========================================================================

Phase 1B walk-forward validation for the STR-Q Liquidity Sweep Reversal strategy.

Methodology:
  1. Read Phase 1A backtest results from CSV (symbol list + baseline metrics)
  2. Fetch full intraday dataset per symbol (same fetchers as Phase 1A)
  3. Split each symbol's data into In-Sample (first 60%) and Out-of-Sample
     (last 40%) by chronological time
  4. Re-run the STR-Q scanner on each segment independently (via data-patching
     context manager that substitutes segment data for the scanner's internal
     fetch calls)
  5. Compare IS vs OOS performance metrics (win rate, avg R, profit factor)
  6. Apply ADR-004 kill floor check: if OOS avg R < 0 and p-value > 0.05 → KILL
  7. Output a markdown report with the walk-forward results

Usage:
    python3 scripts/validation/run_phase1b_q.py
"""

import sys
import json
import datetime
import numpy as np
import pandas as pd
from pathlib import Path

# ── Path setup ──────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation" / "scanners"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))

import scanner_q_liquidity_sweep as scanner_mod
import fetch_intraday_crypto
import fetch_intraday_stocks

# ── Constants ────────────────────────────────────────────────────────────────
RESULTS_DIR = REPO_ROOT / "scripts" / "validation" / "results"
BACKTESTS_DIR = REPO_ROOT / "06-Strategies" / "Backtests"

IS_RATIO = 0.60
OOS_RATIO = 0.40
P_VALUE_THRESHOLD = 0.05
INTERVAL = "5m"
LOOKBACK_BARS = 500

CRYPTO_CSV = RESULTS_DIR / "STR-Q-crypto-phase1a.csv"
STOCK_CSV = RESULTS_DIR / "STR-Q-stocks-phase1a.csv"
REPORT_PATH = BACKTESTS_DIR / "STR-Q-phase1b.md"


# ── Phase 1A Results Loading ────────────────────────────────────────────────

def load_phase1a_results():
    """Load Phase 1A CSV results for both asset classes."""
    crypto_df = pd.read_csv(CRYPTO_CSV) if CRYPTO_CSV.exists() else pd.DataFrame()
    stock_df = pd.read_csv(STOCK_CSV) if STOCK_CSV.exists() else pd.DataFrame()
    return crypto_df, stock_df


def get_symbols_from_results(df):
    """Extract unique symbols from Phase 1A results, preserving order of first appearance."""
    if len(df) == 0:
        return []
    seen = set()
    symbols = []
    for s in df["symbol"].tolist():
        if s not in seen:
            seen.add(s)
            symbols.append(s)
    return symbols


# ── Metrics ───────────────────────────────────────────────────────────────────

def compute_metrics(trades):
    """Compute performance metrics from a list of trade dicts."""
    if not trades:
        return {
            "n_trades": 0,
            "win_rate": 0.0,
            "avg_r": 0.0,
            "median_r": 0.0,
            "sum_r": 0.0,
            "profit_factor": 0.0,
            "max_win": 0.0,
            "max_loss": 0.0,
            "avg_bars_held": 0.0,
        }

    r_values = [float(t["r_multiple"]) for t in trades]
    wins = [r for r in r_values if r > 0]
    losses = [r for r in r_values if r < 0]

    gross_profit = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0

    pf = float("inf") if (gross_loss == 0 and gross_profit > 0) else (
        gross_profit / gross_loss if gross_loss > 0 else 0.0
    )

    bars_held = [t.get("bars_held", 0) for t in trades]

    return {
        "n_trades": len(trades),
        "win_rate": len(wins) / len(r_values) * 100,
        "avg_r": float(np.mean(r_values)),
        "median_r": float(np.median(r_values)),
        "sum_r": float(np.sum(r_values)),
        "profit_factor": pf,
        "max_win": max(r_values),
        "max_loss": min(r_values),
        "avg_bars_held": float(np.mean(bars_held)),
    }


def compute_p_value(r_values):
    """
    One-sample t-test on R-multiples (H0: mean R = 0, two-tailed).

    Returns p-value. If insufficient data, returns 1.0 (no significance).
    """
    if len(r_values) < 2:
        return 1.0

    r_arr = np.array(r_values, dtype=float)
    n = len(r_arr)
    mean_r = float(np.mean(r_arr))
    std_r = float(np.std(r_arr, ddof=1))

    if std_r == 0:
        return 0.0 if mean_r != 0 else 1.0

    t_stat = mean_r / (std_r / np.sqrt(n))

    try:
        from scipy import stats
        p_value = float(2 * stats.t.sf(abs(t_stat), df=n - 1))
    except ImportError:
        # Fallback: normal approximation
        from math import erf, sqrt
        p_value = float(2 * (1 - 0.5 * (1 + erf(abs(t_stat) / sqrt(2)))))

    return p_value


# ── Data Splitting ──────────────────────────────────────────────────────────

def fetch_full_data(symbol, asset_type):
    """Fetch full intraday dataset for a symbol using the standard fetchers."""
    if asset_type == "crypto":
        df = fetch_intraday_crypto.get_intraday_candles(symbol, INTERVAL, LOOKBACK_BARS)
    else:
        df = fetch_intraday_stocks.get_intraday_bars(symbol, INTERVAL, LOOKBACK_BARS)
    return df


def split_by_time(df, is_ratio=IS_RATIO):
    """Split a chronologically sorted dataframe into IS and OOS segments."""
    if len(df) < 10:
        return df, pd.DataFrame()

    df = df.sort_values("timestamp").reset_index(drop=True)
    split_idx = int(len(df) * is_ratio)

    # Ensure OOS has at least some bars
    if split_idx >= len(df) - 10:
        split_idx = max(len(df) - 10, int(len(df) * is_ratio))

    is_df = df.iloc[:split_idx].reset_index(drop=True)
    oos_df = df.iloc[split_idx:].reset_index(drop=True)
    return is_df, oos_df


# ── Segment Level Computation ──────────────────────────────────────────────

def compute_daily_levels_from_df(df):
    """
    Compute prior-day and current-day OHLC levels from an intraday dataframe.
    Mirrors the logic in fetch_intraday_crypto.get_daily_levels.
    """
    if len(df) < 10:
        return {}

    df = df.copy()
    df["date"] = df["timestamp"].dt.date
    daily = df.groupby("date").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
    }).reset_index()

    if len(daily) < 2:
        return {}

    prior = daily.iloc[-2]
    current = daily.iloc[-1]

    return {
        "prior_high": float(prior["high"]),
        "prior_low": float(prior["low"]),
        "prior_close": float(prior["close"]),
        "current_open": float(current["open"]),
        "current_high": float(current["high"]),
        "current_low": float(current["low"]),
        "prior_date": str(prior["date"]),
        "current_date": str(current["date"]),
    }


def compute_session_levels_from_df(df):
    """
    Compute trading session levels from an intraday dataframe.
    Mirrors the logic in fetch_intraday_stocks.get_session_levels.
    """
    if len(df) == 0:
        return {}

    df = df.copy()
    today = df["timestamp"].dt.date.iloc[-1]
    session_df = df[df["timestamp"].dt.date == today].copy()

    # Filter to RTH for stocks (13:30–20:00 UTC = 9:30 AM – 4:00 PM ET)
    if len(session_df) > 0:
        session_utc_hour = session_df["timestamp"].dt.hour
        rth_mask = (session_utc_hour >= 13) & (session_utc_hour < 20)
        rth_df = session_df[rth_mask]
        if len(rth_df) > 0:
            session_df = rth_df

    if len(session_df) == 0:
        return {}

    return {
        "session_open": float(session_df["open"].iloc[0]),
        "session_high": float(session_df["high"].max()),
        "session_low": float(session_df["low"].min()),
        "session_close": float(session_df["close"].iloc[-1]),
        "session_time": str(session_df["timestamp"].iloc[-1]),
        "bars": len(session_df),
    }


# ── Data Patching Context Manager ──────────────────────────────────────────

class SegmentDataPatcher:
    """
    Context manager that temporarily patches the scanner module's data-fetch
    function bindings so that scan_ticker_intraday operates on a specific data
    segment instead of fetching fresh data from the network.

    The scanner imports these at module level:
      - get_intraday_candles  (crypto)
      - get_crypto_daily_levels
      - get_intraday_bars     (stocks)
      - get_stock_daily_levels
      - get_session_levels

    We replace them in the scanner module's namespace for the duration of the
    context, then restore originals on exit.
    """

    def __init__(self, asset_type, symbol, segment_df, interval=INTERVAL):
        self.asset_type = asset_type
        self.symbol = symbol.upper()
        self.segment_df = segment_df
        self.interval = interval
        self._originals = {}

    def __enter__(self):
        # Snapshot originals from the scanner module
        self._originals = {
            "get_intraday_candles": scanner_mod.get_intraday_candles,
            "get_crypto_daily_levels": scanner_mod.get_crypto_daily_levels,
            "get_intraday_bars": scanner_mod.get_intraday_bars,
            "get_stock_daily_levels": scanner_mod.get_stock_daily_levels,
            "get_session_levels": scanner_mod.get_session_levels,
        }

        segment_df = self.segment_df
        symbol = self.symbol
        originals = self._originals

        if self.asset_type == "crypto":
            def patched_candles(sym, interval="5m", lookback_bars=500, use_cache=True):
                if sym.upper() == symbol:
                    return segment_df.copy()
                return originals["get_intraday_candles"](sym, interval, lookback_bars, use_cache)

            def patched_crypto_levels(sym):
                if sym.upper() == symbol:
                    return compute_daily_levels_from_df(segment_df)
                return originals["get_crypto_daily_levels"](sym)

            scanner_mod.get_intraday_candles = patched_candles
            scanner_mod.get_crypto_daily_levels = patched_crypto_levels
        else:
            def patched_bars(sym, interval="5m", lookback_bars=500, use_cache=True):
                if sym.upper() == symbol:
                    return segment_df.copy()
                return originals["get_intraday_bars"](sym, interval, lookback_bars, use_cache)

            def patched_stock_levels(sym):
                if sym.upper() == symbol:
                    return compute_daily_levels_from_df(segment_df)
                return originals["get_stock_daily_levels"](sym)

            def patched_session_levels(sym, interval="5m"):
                if sym.upper() == symbol:
                    return compute_session_levels_from_df(segment_df)
                return originals["get_session_levels"](sym, interval)

            scanner_mod.get_intraday_bars = patched_bars
            scanner_mod.get_stock_daily_levels = patched_stock_levels
            scanner_mod.get_session_levels = patched_session_levels

        return self

    def __exit__(self, *exc_info):
        for name, func in self._originals.items():
            setattr(scanner_mod, name, func)


# ── Segment Scanner ─────────────────────────────────────────────────────────

def scan_segment(symbol, asset_type, segment_df):
    """Run the STR-Q scanner on a specific data segment."""
    if len(segment_df) < 50:
        return []

    with SegmentDataPatcher(asset_type, symbol, segment_df):
        trades = scanner_mod.scan_ticker_intraday(
            symbol, INTERVAL, asset_type, LOOKBACK_BARS
        )
    return trades


# ── Main Walk-Forward Runner ───────────────────────────────────────────────

def run_walk_forward(symbols, asset_type, phase1a_df):
    """Run walk-forward validation for a list of symbols of one asset type."""
    results = []

    for sym in symbols:
        print(f"  [{asset_type}] {sym}...", end=" ")

        # Fetch full data
        full_df = fetch_full_data(sym, asset_type)
        if len(full_df) < 50:
            print(f"insufficient data ({len(full_df)} bars)")
            results.append({
                "symbol": sym,
                "asset_type": asset_type,
                "n_bars": len(full_df),
                "is_bars": 0,
                "oos_bars": 0,
                "is_trades": [],
                "oos_trades": [],
                "is_metrics": compute_metrics([]),
                "oos_metrics": compute_metrics([]),
                "p_value": 1.0,
                "verdict": "INSUFFICIENT DATA",
            })
            continue

        # Split
        is_df, oos_df = split_by_time(full_df, IS_RATIO)
        split_time = (
            oos_df["timestamp"].iloc[0]
            if len(oos_df) > 0
            else is_df["timestamp"].iloc[-1]
        )

        print(f"{len(full_df)} bars → IS:{len(is_df)} OOS:{len(oos_df)}", end=" ")

        # Run scanner on each segment
        is_trades = scan_segment(sym, asset_type, is_df)
        oos_trades = scan_segment(sym, asset_type, oos_df)

        is_metrics = compute_metrics(is_trades)
        oos_metrics = compute_metrics(oos_trades)

        # P-value on OOS R-multiples
        oos_r = [float(t["r_multiple"]) for t in oos_trades]
        p_value = compute_p_value(oos_r)

        # ADR-004 kill floor check
        if oos_metrics["n_trades"] == 0:
            verdict = "INSUFFICIENT DATA"
        elif oos_metrics["avg_r"] < 0 and p_value > P_VALUE_THRESHOLD:
            verdict = "KILL"
        elif oos_metrics["avg_r"] > 0 and p_value <= P_VALUE_THRESHOLD:
            verdict = "CONFIRMED"
        elif oos_metrics["avg_r"] > 0:
            verdict = "WATCH (positive but not significant)"
        else:
            verdict = "WATCH (non-significant)"

        print(
            f"IS:{is_metrics['n_trades']}trades R={is_metrics['avg_r']:.3f} | "
            f"OOS:{oos_metrics['n_trades']}trades R={oos_metrics['avg_r']:.3f} | "
            f"p={p_value:.4f} → {verdict}"
        )

        results.append({
            "symbol": sym,
            "asset_type": asset_type,
            "n_bars": len(full_df),
            "is_bars": len(is_df),
            "oos_bars": len(oos_df),
            "split_time": str(split_time),
            "is_trades": is_trades,
            "oos_trades": oos_trades,
            "is_metrics": is_metrics,
            "oos_metrics": oos_metrics,
            "p_value": p_value,
            "verdict": verdict,
        })

    return results


# ── Aggregate Metrics ──────────────────────────────────────────────────────

def aggregate_segment(all_results, segment_key):
    """Aggregate all trades from a segment (IS or OOS) across all symbols."""
    all_trades = []
    for r in all_results:
        all_trades.extend(r[segment_key])
    return all_trades


# ── Report Generation ──────────────────────────────────────────────────────

def generate_report(crypto_results, stock_results, crypto_1a, stock_1a):
    """Generate the markdown walk-forward report."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Aggregate IS and OOS trades across all symbols and asset classes
    all_results = crypto_results + stock_results
    is_all = aggregate_segment(all_results, "is_trades")
    oos_all = aggregate_segment(all_results, "oos_trades")
    is_metrics = compute_metrics(is_all)
    oos_metrics = compute_metrics(oos_all)

    oos_r_all = [float(t["r_multiple"]) for t in oos_all]
    p_value = compute_p_value(oos_r_all)

    # Per asset class aggregates
    crypto_is = aggregate_segment(crypto_results, "is_trades")
    crypto_oos = aggregate_segment(crypto_results, "oos_trades")
    crypto_is_m = compute_metrics(crypto_is)
    crypto_oos_m = compute_metrics(crypto_oos)
    crypto_p = compute_p_value([float(t["r_multiple"]) for t in crypto_oos])

    stock_is = aggregate_segment(stock_results, "is_trades")
    stock_oos = aggregate_segment(stock_results, "oos_trades")
    stock_is_m = compute_metrics(stock_is)
    stock_oos_m = compute_metrics(stock_oos)
    stock_p = compute_p_value([float(t["r_multiple"]) for t in stock_oos])

    # Phase 1A baseline
    p1a_total = len(crypto_1a) + len(stock_1a)
    p1a_all = pd.concat([crypto_1a, stock_1a], ignore_index=True) if p1a_total > 0 else pd.DataFrame()
    p1a_avg_r = float(p1a_all["r_multiple"].mean()) if p1a_total > 0 else 0.0
    p1a_win_rate = float((p1a_all["r_multiple"] > 0).mean() * 100) if p1a_total > 0 else 0.0
    p1a_n = p1a_total

    # Overall verdict
    if oos_metrics["n_trades"] == 0:
        overall_verdict = "INSUFFICIENT DATA"
        verdict_reason = "No OOS trades generated — cannot evaluate walk-forward edge."
    elif oos_metrics["avg_r"] < 0 and p_value > P_VALUE_THRESHOLD:
        overall_verdict = "KILL"
        verdict_reason = (
            f"OOS avg R = {oos_metrics['avg_r']:.3f} (< 0) and p-value = {p_value:.4f} "
            f"(> {P_VALUE_THRESHOLD}). The edge does not survive out-of-sample. "
            f"Per ADR-004 kill floor: flag for KILL."
        )
    elif oos_metrics["avg_r"] > 0 and p_value <= P_VALUE_THRESHOLD:
        overall_verdict = "PASS"
        verdict_reason = (
            f"OOS avg R = {oos_metrics['avg_r']:.3f} (> 0) and p-value = {p_value:.4f} "
            f"(<= {P_VALUE_THRESHOLD}). Edge is confirmed out-of-sample."
        )
    elif oos_metrics["avg_r"] > 0:
        overall_verdict = "WATCH"
        verdict_reason = (
            f"OOS avg R = {oos_metrics['avg_r']:.3f} (> 0) but p-value = {p_value:.4f} "
            f"(> {P_VALUE_THRESHOLD}). Positive but not statistically significant."
        )
    else:
        overall_verdict = "WATCH"
        verdict_reason = (
            f"OOS avg R = {oos_metrics['avg_r']:.3f}. Edge is non-significant."
        )

    # Build per-symbol table rows
    def symbol_table(results):
        rows = []
        for r in results:
            im = r["is_metrics"]
            om = r["oos_metrics"]
            rows.append(
                f"| {r['symbol']} | {im['n_trades']} | {im['avg_r']:+.3f} | "
                f"{im['win_rate']:.1f}% | {im['profit_factor']:.2f} | "
                f"{om['n_trades']} | {om['avg_r']:+.3f} | {om['win_rate']:.1f}% | "
                f"{om['profit_factor']:.2f} | {r['p_value']:.4f} | {r['verdict']} |"
            )
        return "\n".join(rows)

    # Per-symbol crypto/stock breakdown for direction
    def direction_table(results, segment_key):
        trades = aggregate_segment(results, segment_key)
        if not trades:
            return "n/a"
        df = pd.DataFrame(trades)
        lines = []
        for direction in ["bullish", "bearish"]:
            subset = df[df["direction"] == direction]
            if len(subset) == 0:
                continue
            m = compute_metrics(subset.to_dict("records"))
            lines.append(
                f"  - **{direction}**: {m['n_trades']} trades, WR={m['win_rate']:.1f}%, "
                f"avg R={m['avg_r']:+.3f}, PF={m['profit_factor']:.2f}"
            )
        return "\n".join(lines)

    # IS/OOS degradation summary
    degradation = ""
    if is_metrics["n_trades"] > 0 and oos_metrics["n_trades"] > 0:
        r_deg = oos_metrics["avg_r"] - is_metrics["avg_r"]
        wr_deg = oos_metrics["win_rate"] - is_metrics["win_rate"]
        degradation = (
            f"- **Avg R degradation**: {r_deg:+.3f} "
            f"(IS: {is_metrics['avg_r']:+.3f} → OOS: {oos_metrics['avg_r']:+.3f})\n"
            f"- **Win rate degradation**: {wr_deg:+.1f}pp "
            f"(IS: {is_metrics['win_rate']:.1f}% → OOS: {oos_metrics['win_rate']:.1f}%)"
        )

    report = f"""---
type: backtest-result
strategy_id: STR-Q
strategy_name: Liquidity Sweep Reversal
phase: 1B
walk_forward: true
asset_class: both
direction: bidirectional
universe: 8 crypto + 8 stocks
period_start: 2026-08-06
period_end: 2026-08-15
is_ratio: {IS_RATIO}
oos_ratio: {OOS_RATIO}
verdict: {overall_verdict}
verdict_reason: "{verdict_reason}"
data_limitations: "Short intraday history (~2 days crypto, ~8 days stocks, 5m bars). Small sample sizes limit statistical power."
produced_by: "Phase 1B Walk-Forward Script (run_phase1b_q.py)"
generated: {now}
tags: [backtest, walkforward, STR-Q, liquidity-sweep, crypto, stocks, {overall_verdict.lower().replace(' ', '-')}]
topic: strategies
confidence: moderate
has_quotes: false
source: HermesForge Strategies
---
# STR-Q Phase 1B Walk-Forward Validation Results

## Method
Per-symbol walk-forward validation of the STR-Q Liquidity Sweep Reversal strategy.

1. **Data**: Full intraday 5m bars fetched per symbol (same fetchers as Phase 1A)
2. **Split**: Each symbol's data split chronologically — In-Sample (first 60%) and Out-of-Sample (last 40%)
3. **Re-scan**: The STR-Q scanner re-run independently on each segment with identical parameters
4. **Comparison**: IS vs OOS metrics compared (win rate, avg R, profit factor)
5. **ADR-004 kill floor**: If OOS avg R < 0 and p-value > 0.05 → flag for KILL
6. **P-value**: One-sample t-test on OOS R-multiples (H0: mean R = 0, two-tailed)

**Note**: This is intraday data with limited history (~2 days crypto, ~8 days stocks at 5m resolution).
Sample sizes per segment are small, which limits statistical power. Results should be interpreted
as indicative rather than definitive.

## Phase 1A Baseline (Frictionless)
- **Total signals**: {p1a_n}
- **Avg R**: {p1a_avg_r:+.3f}
- **Win rate**: {p1a_win_rate:.1f}%

## Aggregate Results (All Symbols Combined)

### IS vs OOS Comparison

| Metric | In-Sample (60%) | Out-of-Sample (40%) |
|--------|----------------:|--------------------:|
| Trades | {is_metrics['n_trades']} | {oos_metrics['n_trades']} |
| Avg R | {is_metrics['avg_r']:+.3f} | {oos_metrics['avg_r']:+.3f} |
| Median R | {is_metrics['median_r']:+.3f} | {oos_metrics['median_r']:+.3f} |
| Sum R | {is_metrics['sum_r']:+.3f} | {oos_metrics['sum_r']:+.3f} |
| Win Rate | {is_metrics['win_rate']:.1f}% | {oos_metrics['win_rate']:.1f}% |
| Profit Factor | {is_metrics['profit_factor']:.2f} | {oos_metrics['profit_factor']:.2f} |
| Max Win | {is_metrics['max_win']:+.3f}R | {oos_metrics['max_win']:+.3f}R |
| Max Loss | {is_metrics['max_loss']:+.3f}R | {oos_metrics['max_loss']:+.3f}R |
| Avg Bars Held | {is_metrics['avg_bars_held']:.1f} | {oos_metrics['avg_bars_held']:.1f} |

### OOS Statistical Significance
- **N = {oos_metrics['n_trades']} signals**
- **Mean R = {oos_metrics['avg_r']:+.3f}**
- **p-value = {p_value:.4f}** (one-sample t-test, H0: mean R = 0)
- **ADR-004 kill floor**: OOS avg R {'<' if oos_metrics['avg_r'] < 0 else '>='} 0 and p-value {'>' if p_value > P_VALUE_THRESHOLD else '<='} {P_VALUE_THRESHOLD}

{degradation}

## Per-Symbol Results: Crypto

| Symbol | IS N | IS Avg R | IS Win% | IS PF | OOS N | OOS Avg R | OOS Win% | OOS PF | p-value | Verdict |
|--------|------|----------|---------|-------|-------|-----------|----------|--------|---------|---------|
{symbol_table(crypto_results)}

### Crypto Aggregate
| Segment | N | Avg R | Win Rate | Profit Factor |
|---------|---|-------|----------|---------------|
| IS | {crypto_is_m['n_trades']} | {crypto_is_m['avg_r']:+.3f} | {crypto_is_m['win_rate']:.1f}% | {crypto_is_m['profit_factor']:.2f} |
| OOS | {crypto_oos_m['n_trades']} | {crypto_oos_m['avg_r']:+.3f} | {crypto_oos_m['win_rate']:.1f}% | {crypto_oos_m['profit_factor']:.2f} |
| p-value | | | | {crypto_p:.4f} |

## Per-Symbol Results: Stocks

| Symbol | IS N | IS Avg R | IS Win% | IS PF | OOS N | OOS Avg R | OOS Win% | OOS PF | p-value | Verdict |
|--------|------|----------|---------|-------|-------|-----------|----------|--------|---------|---------|
{symbol_table(stock_results)}

### Stocks Aggregate
| Segment | N | Avg R | Win Rate | Profit Factor |
|---------|---|-------|----------|---------------|
| IS | {stock_is_m['n_trades']} | {stock_is_m['avg_r']:+.3f} | {stock_is_m['win_rate']:.1f}% | {stock_is_m['profit_factor']:.2f} |
| OOS | {stock_oos_m['n_trades']} | {stock_oos_m['avg_r']:+.3f} | {stock_oos_m['win_rate']:.1f}% | {stock_oos_m['profit_factor']:.2f} |
| p-value | | | | {stock_p:.4f} |

## Direction Breakdown (All Symbols)

### In-Sample
{direction_table(all_results, 'is_trades')}

### Out-of-Sample
{direction_table(all_results, 'oos_trades')}

## Assessment

### Data Limitations
- **Crypto**: ~2 days of 5m bars (500 bars per symbol). IS segment ~300 bars, OOS ~200 bars.
- **Stocks**: ~8 days of 5m bars (500 bars per symbol). IS segment ~300 bars, OOS ~200 bars.
- These short windows mean few trades per symbol per segment, limiting statistical power.
- The p-value from a one-sample t-test on small samples should be interpreted cautiously.

### Comparison to Phase 1A

| Metric | Phase 1A (frictionless, full) | Phase 1B IS (60%) | Phase 1B OOS (40%) |
|--------|------------------------------|-------------------|---------------------|
| Avg R | {p1a_avg_r:+.3f} | {is_metrics['avg_r']:+.3f} | {oos_metrics['avg_r']:+.3f} |
| N | {p1a_n} | {is_metrics['n_trades']} | {oos_metrics['n_trades']} |
| Win Rate | {p1a_win_rate:.1f}% | {is_metrics['win_rate']:.1f}% | {oos_metrics['win_rate']:.1f}% |

## Overall Verdict: {overall_verdict}

{verdict_reason}

Per ADR-004 kill floor check:
- **OOS avg R**: {oos_metrics['avg_r']:+.3f} ({'< 0 → losing' if oos_metrics['avg_r'] < 0 else '>= 0 → not losing'})
- **p-value**: {p_value:.4f} ({'> 0.05 → not significant' if p_value > P_VALUE_THRESHOLD else '<= 0.05 → significant'})
- **Kill condition** (OOS avg R < 0 AND p > 0.05): {'TRIGGERED → KILL' if (oos_metrics['avg_r'] < 0 and p_value > P_VALUE_THRESHOLD) else 'NOT TRIGGERED'}

## Related
- [[ADR-004-Phase1-Validation-Framework]]
- Phase 1A results: `scripts/validation/results/STR-Q-crypto-phase1a.csv`, `STR-Q-stocks-phase1a.csv`
- Scanner: `scripts/validation/scanners/scanner_q_liquidity_sweep.py`
"""

    return report


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("STR-Q Phase 1B Walk-Forward Validation")
    print("=" * 60)

    # Step 1: Load Phase 1A results
    print("\n[1] Loading Phase 1A results...")
    crypto_1a, stock_1a = load_phase1a_results()
    print(f"  Crypto trades: {len(crypto_1a)}")
    print(f"  Stock trades: {len(stock_1a)}")

    crypto_symbols = get_symbols_from_results(crypto_1a)
    stock_symbols = get_symbols_from_results(stock_1a)
    print(f"  Crypto symbols: {crypto_symbols}")
    print(f"  Stock symbols: {stock_symbols}")

    # Step 2-4: Fetch data, split, re-scan
    print("\n[2] Running walk-forward on CRYPTO...")
    crypto_results = run_walk_forward(crypto_symbols, "crypto", crypto_1a)

    print("\n[3] Running walk-forward on STOCKS...")
    stock_results = run_walk_forward(stock_symbols, "stock", stock_1a)

    # Step 5-6: Generate report
    print("\n[4] Generating report...")
    report = generate_report(crypto_results, stock_results, crypto_1a, stock_1a)

    # Save report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    print(f"\nReport saved → {REPORT_PATH}")

    # Save segment trades as CSV for traceability
    all_results = crypto_results + stock_results
    is_trades_flat = []
    oos_trades_flat = []
    for r in all_results:
        for t in r["is_trades"]:
            t_copy = dict(t)
            t_copy["segment"] = "IS"
            is_trades_flat.append(t_copy)
        for t in r["oos_trades"]:
            t_copy = dict(t)
            t_copy["segment"] = "OOS"
            oos_trades_flat.append(t_copy)

    all_segment_trades = is_trades_flat + oos_trades_flat
    if all_segment_trades:
        trades_df = pd.DataFrame(all_segment_trades)
        trades_csv = RESULTS_DIR / "STR-Q-phase1b-segment-trades.csv"
        trades_df.to_csv(trades_csv, index=False)
        print(f"Segment trades saved → {trades_csv}")

    # Print summary
    all_is = aggregate_segment(all_results, "is_trades")
    all_oos = aggregate_segment(all_results, "oos_trades")
    is_m = compute_metrics(all_is)
    oos_m = compute_metrics(all_oos)
    p_val = compute_p_value([float(t["r_multiple"]) for t in all_oos])

    print(f"\n{'=' * 60}")
    print("PHASE 1B SUMMARY — STR-Q Liquidity Sweep")
    print(f"{'=' * 60}")
    print(f"  IS:  {is_m['n_trades']} trades, avg R={is_m['avg_r']:+.3f}, WR={is_m['win_rate']:.1f}%, PF={is_m['profit_factor']:.2f}")
    print(f"  OOS: {oos_m['n_trades']} trades, avg R={oos_m['avg_r']:+.3f}, WR={oos_m['win_rate']:.1f}%, PF={oos_m['profit_factor']:.2f}")
    print(f"  p-value (OOS): {p_val:.4f}")

    if oos_m["n_trades"] == 0:
        verdict = "INSUFFICIENT DATA"
    elif oos_m["avg_r"] < 0 and p_val > P_VALUE_THRESHOLD:
        verdict = "KILL"
    elif oos_m["avg_r"] > 0 and p_val <= P_VALUE_THRESHOLD:
        verdict = "PASS"
    elif oos_m["avg_r"] > 0:
        verdict = "WATCH (positive but not significant)"
    else:
        verdict = "WATCH (non-significant)"

    print(f"  Verdict: {verdict}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
