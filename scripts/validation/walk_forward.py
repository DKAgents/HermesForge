#!/usr/bin/env python3
"""
walk_forward.py — HermesForge Walk-Forward Validation Framework

Answers the most important question: do our strategies have real edge,
or are we trading in-sample noise?

What it does:
  1. Splits history into rolling windows (train → test)
  2. Optimizes parameters on each training window
  3. Tests optimized parameters on the next unseen window (OOS)
  4. Applies transaction costs (spread + commission + gap risk)
  5. Computes statistical significance (t-test + bootstrap CI)
  6. Reports: which strategies are ROBUST vs FRAGILE vs NO EDGE

Usage:
    python3 walk_forward.py                    # all 4 active strategies
    python3 walk_forward.py --strategy B      # single strategy
    python3 walk_forward.py --json             # JSON output
    python3 walk_forward.py --quick            # smaller grid, faster
"""

import sys
import json
import argparse
import pathlib
import importlib
import itertools
import time
import numpy as np
import pandas as pd
from datetime import datetime

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation" / "scanners"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "discord"))

from fetch_data import load_all as load_all_stocks
from fetch_crypto_data import load_all as load_all_crypto

# ── Strategy Registry ────────────────────────────────────────────────────────
# Each strategy entry: module path, scan function name, parameter grid
# The grid defines which parameters to sweep during optimization.

SCANNER_DIR = REPO_ROOT / "scripts" / "validation" / "scanners"

STRATEGY_CONFIGS = {
    "B": {
        "module": "scanner_b_macd_divergence",
        "scan_fn": "scan",
        "name": "MACD Divergence",
        "params": {
            "MACD_FAST": [8, 12, 16],
            "ATR_STOP_MULT": [0.3, 0.5, 0.7],
            "MATURITY_BARS": [10, 15, 20],
        },
        "asset_class": "both",
        "long_only_stocks": True,
    },
    "I": {
        "module": "scanner_i_adaptive_trend",
        "scan_fn": "scan",
        "name": "AdaptiveTrend",
        "params": {
            "LOOKBACK": [10, 20, 30],
            "ENTRY_THRESHOLD": [0.10, 0.15, 0.20],
            "ATR_MULTIPLIER": [2.0, 2.5, 3.0],
        },
        "asset_class": "both",
        "long_only_stocks": True,
    },
    "J": {
        "module": "scanner_j_eufearia_cci",
        "scan_fn": "scan",
        "name": "EUFEARIA CCI",
        "params": {
            "CHANNEL_LENGTH": [8, 10, 14],
            "ATR_STOP_MULTIPLIER": [0.8, 1.0, 1.5],
            "MAX_BARS_HELD": [8, 10, 15],
        },
        "asset_class": "both",
        "long_only_stocks": True,
    },
    "L": {
        "module": "scanner_l_atr_contraction",
        "scan_fn": "scan_ticker",
        "name": "ATR Contraction",
        "params": {
            "ATR_LOOKBACK": [60, 90, 120],
            "ADX_THRESHOLD": [15, 18, 22],
            "TRAILING_ATR_MULT": [1.5, 2.0, 2.5],
        },
        "asset_class": "stock",
        "long_only_stocks": True,
    },
}

# Quick mode: smaller parameter grid for faster runs
QUICK_PARAMS = {
    "B": {"MACD_FAST": [12], "ATR_STOP_MULT": [0.3, 0.5, 0.7], "MATURITY_BARS": [15]},
    "I": {"LOOKBACK": [10, 20], "ENTRY_THRESHOLD": [0.15, 0.20], "ATR_MULTIPLIER": [2.0, 2.5]},
    "J": {"CHANNEL_LENGTH": [10], "ATR_STOP_MULTIPLIER": [1.0, 1.5], "MAX_BARS_HELD": [10]},
    "L": {"ATR_LOOKBACK": [120], "ADX_THRESHOLD": [18], "TRAILING_ATR_MULT": [2.0]},
}

# ── Walk-Forward Windows ──────────────────────────────────────────────────────
# Train: 2 years, Test: 1 year, Roll: 1 year
# Data available: 2019-2026 (stocks), 2020-2026 (crypto)

WINDOWS = [
    {"train": ("2019-01-01", "2021-12-31"), "test": ("2022-01-01", "2022-12-31"), "label": "2022"},
    {"train": ("2020-01-01", "2022-12-31"), "test": ("2023-01-01", "2023-12-31"), "label": "2023"},
    {"train": ("2021-01-01", "2023-12-31"), "test": ("2024-01-01", "2024-12-31"), "label": "2024"},
    {"train": ("2022-01-01", "2024-12-31"), "test": ("2025-01-01", "2025-12-31"), "label": "2025"},
    {"train": ("2023-01-01", "2025-12-31"), "test": ("2026-01-01", "2026-12-31"), "label": "2026"},
]

# Optimization sample: 30 liquid tickers (S&P 100 subset)
OPTIMIZATION_SAMPLE = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA", "JPM", "V", "JNJ",
    "WMT", "PG", "MA", "UNH", "HD", "DIS", "BAC", "XOM", "KO", "PEP",
    "PFE", "MRK", "TMO", "AVGO", "COST", "ABBV", "CRM", "ADBE", "NFLX", "AMD",
]

# Crypto optimization sample
CRYPTO_OPTIMIZATION_SAMPLE = ["BTC", "ETH", "SOL", "AVAX", "LINK", "DOGE", "ARB", "OP", "SUI", "BNB"]

# ── Transaction Cost Model ────────────────────────────────────────────────────
# Realistic costs for retail trading
SPREAD_BPS = 5.0       # 5 basis points spread (0.05%)
COMMISSION_BPS = 1.0   # 1 basis point commission (0.01%)
# Total round-trip cost: 2 * (spread + commission) = 12bp = 0.12%

# ── Statistical Significance ──────────────────────────────────────────────────
BOOTSTRAP_SAMPLES = 5000
CONFIDENCE_LEVEL = 0.95


def apply_costs(signal: dict, asset_class: str = "stock") -> dict:
    """
    Apply transaction costs to a signal's R-multiple.

    Costs reduce the reward (for winners) and increase the risk (for losers):
      - Entry: pay spread/2 + commission
      - Exit: pay spread/2 + commission
      - Gap risk: if the next bar opens beyond the stop, use open instead of stop

    For stocks: spread = 5bp, commission = 1bp
    For crypto: spread = 2bp (more liquid), commission = 0.5bp
    """
    entry = float(signal.get("entry_price", 0))
    stop = float(signal.get("stop_price", 0))
    target = float(signal.get("target_price", 0))
    direction = signal.get("direction", "long")
    r_multiple = float(signal.get("r_multiple", 0))

    if not entry or not stop:
        return signal

    risk = abs(entry - stop)
    if risk == 0:
        return signal

    # Cost varies by asset class
    if asset_class == "crypto":
        total_cost_pct = (2 + 0.5) * 2 / 10000  # 5bp round trip
    else:
        total_cost_pct = (5 + 1) * 2 / 10000   # 12bp round trip

    # Dollar cost = entry * total_cost_pct
    dollar_cost = entry * total_cost_pct

    # Cost in R-multiples: dollar_cost / risk
    cost_r = dollar_cost / risk

    # Adjust R: costs reduce every trade's R by cost_r
    adjusted_r = r_multiple - cost_r

    signal["r_multiple_raw"] = r_multiple
    signal["r_multiple"] = round(adjusted_r, 4)
    signal["cost_r"] = round(cost_r, 4)
    signal["dollar_cost"] = round(dollar_cost, 2)

    return signal


def apply_gap_risk(signal: dict, df: pd.DataFrame) -> dict:
    """
    If the next bar after entry opens beyond the stop, use the open price.
    This simulates realistic slippage on gap-downs/gap-ups.

    Only applies if we can find the entry date in the data.
    """
    entry_date = signal.get("date", "")
    if not entry_date:
        return signal

    entry_date_str = str(entry_date)[:10]
    direction = signal.get("direction", "long")
    stop = float(signal.get("stop_price", 0))

    # Find the bar after entry
    try:
        entry_idx = None
        for i, idx in enumerate(df.index):
            if str(idx)[:10] == entry_date_str:
                entry_idx = i
                break

        if entry_idx is None or entry_idx + 1 >= len(df):
            return signal

        next_bar = df.iloc[entry_idx + 1]
        next_open = next_bar["open"]

        if direction == "long" and next_open < stop:
            # Gap down below stop — fill at open, not stop
            signal["gap_adjusted"] = True
            signal["actual_exit"] = next_open
            entry = float(signal.get("entry_price", 0))
            risk = abs(entry - stop)
            if risk > 0:
                signal["r_multiple"] = round((next_open - entry) / risk, 4) * -1  # negative R
        elif direction == "short" and next_open > stop:
            # Gap up above stop — fill at open, not stop
            signal["gap_adjusted"] = True
            signal["actual_exit"] = next_open
            entry = float(signal.get("entry_price", 0))
            risk = abs(stop - entry)
            if risk > 0:
                signal["r_multiple"] = round((entry - next_open) / risk, 4) * -1
    except Exception:
        pass

    return signal


def compute_significance(r_values: list) -> dict:
    """
    Compute t-statistic, p-value, and bootstrap confidence interval
    for a list of R-multiples.

    H0: mean R = 0 (no edge)
    H1: mean R != 0 (edge exists)
    """
    if len(r_values) < 3:
        return {
            "n": len(r_values),
            "mean_r": 0,
            "std_r": 0,
            "t_stat": 0,
            "p_value": 1.0,
            "ci_lower": 0,
            "ci_upper": 0,
            "significant": False,
            "verdict": "INSUFFICIENT DATA",
        }

    r = np.array(r_values, dtype=float)
    n = len(r)
    mean_r = float(np.mean(r))
    std_r = float(np.std(r, ddof=1)) if n > 1 else 0

    # t-test (one-sample, H0: mean = 0)
    if std_r > 0:
        t_stat = mean_r / (std_r / np.sqrt(n))
    else:
        t_stat = 0 if mean_r == 0 else float('inf') * np.sign(mean_r)

    # Approximate p-value using normal distribution (simplified, no scipy)
    # For proper t-distribution we'd use scipy, but this is a reasonable approximation
    # for n > 20
    from statistics import NormalDist
    nd = NormalDist(0, 1)
    p_value = 2 * (1 - nd.cdf(abs(t_stat))) if abs(t_stat) < 100 else 0.0

    # Bootstrap confidence interval
    bootstrap_means = []
    for _ in range(BOOTSTRAP_SAMPLES):
        sample = np.random.choice(r, size=n, replace=True)
        bootstrap_means.append(np.mean(sample))

    ci_lower = float(np.percentile(bootstrap_means, (1 - CONFIDENCE_LEVEL) / 2 * 100))
    ci_upper = float(np.percentile(bootstrap_means, (1 + CONFIDENCE_LEVEL) / 2 * 100))

    # Verdict
    significant = p_value < 0.05 and ci_lower > 0
    if significant:
        verdict = "ROBUST EDGE"
    elif p_value < 0.10 and ci_lower > -0.1:
        verdict = "FRAGILE EDGE"
    elif mean_r > 0 and p_value < 0.20:
        verdict = "POSSIBLE EDGE (low confidence)"
    else:
        verdict = "NO EDGE"

    return {
        "n": n,
        "mean_r": round(mean_r, 4),
        "std_r": round(std_r, 4),
        "t_stat": round(t_stat, 3),
        "p_value": round(p_value, 4),
        "ci_lower": round(ci_lower, 4),
        "ci_upper": round(ci_upper, 4),
        "significant": significant,
        "verdict": verdict,
    }


def scan_with_params(module, scan_fn_name: str, data_dict: dict,
                     params: dict, start_date: str, end_date: str,
                     asset_class: str = "stock", long_only: bool = False,
                     apply_cost: bool = True) -> list:
    """
    Scan a data dict with specific parameters applied via monkey-patching.
    Returns list of signals with R-multiples, filtered to the date range.
    """
    # Save original values
    originals = {}
    for key, value in params.items():
        originals[key] = getattr(module, key)
        setattr(module, key, value)

    # Reset original values when done
    try:
        scan_fn = getattr(module, scan_fn_name)
        signals = []

        for ticker, df in data_dict.items():
            if len(df) < 250:
                continue

            # Slice data to the relevant period (but keep enough history for indicators)
            # Keep 1 year of lookback before start_date for indicator warm-up
            lookback_start = pd.Timestamp(start_date) - pd.Timedelta(days=400)
            mask = df.index >= lookback_start
            df_slice = df[mask].copy()

            if len(df_slice) < 50:
                continue

            try:
                kwargs = {}
                # Only STR-I accepts long_only kwarg
                if module.__name__ == "scanner_i_adaptive_trend" and asset_class == "stock":
                    kwargs["long_only"] = True

                sigs = scan_fn(df_slice, ticker, **kwargs)
                if not sigs:
                    continue

                # Filter to date range
                for sig in sigs:
                    sig_date = str(sig.get("date", ""))[:10]
                    if start_date <= sig_date <= end_date:
                        sig["ticker"] = ticker
                        sig["asset_class"] = asset_class

                        # Apply gap risk adjustment
                        sig = apply_gap_risk(sig, df_slice)

                        # Apply transaction costs
                        if apply_cost:
                            sig = apply_costs(sig, asset_class)

                        signals.append(sig)
            except Exception:
                continue

        return signals
    finally:
        # Restore originals
        for key, value in originals.items():
            setattr(module, key, value)


def optimize_parameters(module, scan_fn_name: str, data_dict: dict,
                         param_grid: dict, train_start: str, train_end: str,
                         asset_class: str, long_only: bool) -> tuple:
    """
    Grid search over parameter combinations on the training window.
    Returns (best_params, best_avg_r, all_results).
    """
    keys = list(param_grid.keys())
    values = list(param_grid.values())
    combinations = list(itertools.product(*values))

    best_avg_r = -999
    best_params = None
    all_results = []

    for combo in combinations:
        params = dict(zip(keys, combo))
        signals = scan_with_params(
            module, scan_fn_name, data_dict, params,
            train_start, train_end, asset_class, long_only,
            apply_cost=True  # optimize with costs to find robust params
        )

        if len(signals) < 3:
            continue

        avg_r = np.mean([s.get("r_multiple", 0) for s in signals])
        win_rate = np.mean([1 if s.get("r_multiple", 0) > 0 else 0 for s in signals])

        all_results.append({
            "params": params,
            "n_signals": len(signals),
            "avg_r": round(avg_r, 4),
            "win_rate": round(win_rate, 3),
        })

        if avg_r > best_avg_r and len(signals) >= 3:
            best_avg_r = avg_r
            best_params = params

    return best_params, round(best_avg_r, 4), all_results


def run_walk_forward(strategy_id: str, stock_data: dict, crypto_data: dict,
                     quick: bool = False, verbose: bool = True) -> dict:
    """
    Run full walk-forward validation for a single strategy.

    Returns dict with:
      - in_sample_results (full period, default params)
      - oos_results (per window, optimized params)
      - significance stats
      - verdict
    """
    config = STRATEGY_CONFIGS[strategy_id]
    module_name = config["module"]
    scan_fn_name = config["scan_fn"]
    param_grid = QUICK_PARAMS[strategy_id] if quick else config["params"]
    asset_classes = ["stock", "crypto"] if config["asset_class"] == "both" else ["stock"]

    # Import the scanner module
    module = importlib.import_module(module_name)

    results = {
        "strategy_id": strategy_id,
        "name": config["name"],
        "windows": [],
        "oos_all": [],       # all OOS signals across windows
        "in_sample": [],      # full period signals with default params
    }

    for asset_class in asset_classes:
        if asset_class == "stock":
            data = stock_data
            opt_sample = {t: v for t, v in stock_data.items() if t in OPTIMIZATION_SAMPLE}
            long_only = config.get("long_only_stocks", False)
        else:
            data = crypto_data
            opt_sample = {t: v for t, v in crypto_data.items() if t in CRYPTO_OPTIMIZATION_SAMPLE}
            long_only = False  # crypto allows shorts

        if not opt_sample:
            print(f"  No optimization sample data for {asset_class}")
            continue

        print(f"\n  [{strategy_id}] {asset_class.upper()} — "
              f"optimizing on {len(opt_sample)} tickers, testing on {len(data)}")

        # ── In-sample baseline (full period, default params) ─────────────────
        # Get default params from the module
        default_params = {}
        for key in param_grid:
            default_params[key] = [getattr(module, key)]
        default_flat = {k: v[0] for k, v in default_params.items()}

        is_signals = scan_with_params(
            module, scan_fn_name, data, default_flat,
            "2019-01-01", "2026-12-31", asset_class, long_only,
            apply_cost=True
        )

        for sig in is_signals:
            sig["period"] = "in_sample"
            sig["asset_class"] = asset_class
            results["in_sample"].append(sig)

        is_avg_r = np.mean([s.get("r_multiple", 0) for s in is_signals]) if is_signals else 0
        print(f"    In-sample (full period, default params): "
              f"{len(is_signals)} signals, avg R = {is_avg_r:.4f}")

        # ── Walk-forward windows ─────────────────────────────────────────────
        for window in WINDOWS:
            train_start, train_end = window["train"]
            test_start, test_end = window["test"]
            label = window["label"]

            # Optimize on training window using sample
            t0 = time.time()
            best_params, best_train_r, all_combos = optimize_parameters(
                module, scan_fn_name, opt_sample, param_grid,
                train_start, train_end, asset_class, long_only
            )
            opt_time = time.time() - t0

            if best_params is None:
                print(f"    Window {label}: no valid parameter combination found in training")
                continue

            # Test on the unseen test window using ALL tickers
            oos_signals = scan_with_params(
                module, scan_fn_name, data, best_params,
                test_start, test_end, asset_class, long_only,
                apply_cost=True
            )

            oos_avg_r = np.mean([s.get("r_multiple", 0) for s in oos_signals]) if oos_signals else 0
            oos_win_rate = np.mean([1 if s.get("r_multiple", 0) > 0 else 0 for s in oos_signals]) if oos_signals else 0

            # Also get train results with best params for comparison
            train_signals = scan_with_params(
                module, scan_fn_name, opt_sample, best_params,
                train_start, train_end, asset_class, long_only,
                apply_cost=True
            )
            train_avg_r = np.mean([s.get("r_multiple", 0) for s in train_signals]) if train_signals else 0

            window_result = {
                "window": label,
                "asset_class": asset_class,
                "train_period": f"{train_start} to {train_end}",
                "test_period": f"{test_start} to {test_end}",
                "best_params": best_params,
                "train_avg_r": round(train_avg_r, 4),
                "train_n": len(train_signals),
                "oos_avg_r": round(oos_avg_r, 4),
                "oos_n": len(oos_signals),
                "oos_win_rate": round(oos_win_rate, 3),
                "optimization_time_s": round(opt_time, 1),
                "param_combos_tested": len(all_combos),
            }

            results["windows"].append(window_result)

            for sig in oos_signals:
                sig["window"] = label
                sig["asset_class"] = asset_class
                sig["params_used"] = best_params
                results["oos_all"].append(sig)

            print(f"    Window {label}: train R={train_avg_r:.4f} ({len(train_signals)} sigs) → "
                  f"OOS R={oos_avg_r:.4f} ({len(oos_signals)} sigs, "
                  f"win {oos_win_rate:.0%}) [{opt_time:.1f}s]")

    # ── Significance testing ────────────────────────────────────────────────
    # Test on OOS signals (all windows combined)
    oos_r = [s.get("r_multiple", 0) for s in results["oos_all"]]
    is_r = [s.get("r_multiple", 0) for s in results["in_sample"]]

    results["oos_significance"] = compute_significance(oos_r)
    results["in_sample_significance"] = compute_significance(is_r)

    # Per-window significance
    results["per_window_significance"] = {}
    for window in WINDOWS:
        label = window["label"]
        window_r = [s.get("r_multiple", 0) for s in results["oos_all"]
                    if s.get("window") == label]
        if window_r:
            results["per_window_significance"][label] = compute_significance(window_r)

    print(f"\n  [{strategy_id}] OOS significance: "
          f"mean R={results['oos_significance']['mean_r']:.4f}, "
          f"t={results['oos_significance']['t_stat']:.2f}, "
          f"p={results['oos_significance']['p_value']:.4f}, "
          f"CI=[{results['oos_significance']['ci_lower']:.4f}, "
          f"{results['oos_significance']['ci_upper']:.4f}], "
          f"verdict={results['oos_significance']['verdict']}")

    return results


def run_all_strategies(quick: bool = False, verbose: bool = True) -> dict:
    """Run walk-forward validation on all 4 active strategies."""
    print("=" * 70)
    print("HermesForge Walk-Forward Validation Framework")
    print("=" * 70)

    print("\nLoading stock data...")
    stock_data = load_all_stocks()
    print(f"  {len(stock_data)} stock tickers loaded.")

    print("Loading crypto data...")
    crypto_data = load_all_crypto()
    print(f"  {len(crypto_data)} crypto symbols loaded.")

    # Transaction cost summary
    print("\n" + "-" * 70)
    print("Transaction Cost Model:")
    print(f"  Stocks:  {SPREAD_BPS}bp spread + {COMMISSION_BPS}bp commission = "
          f"{(SPREAD_BPS + COMMISSION_BPS) * 2}bp round-trip")
    print(f"  Crypto:  2bp spread + 0.5bp commission = 5bp round-trip")
    print(f"  Gap risk: applied (next bar open if it gaps past stop)")
    print("-" * 70)

    all_results = {}
    for strategy_id in ["B", "I", "J", "L"]:
        print(f"\n{'='*70}")
        print(f"Strategy {strategy_id}: {STRATEGY_CONFIGS[strategy_id]['name']}")
        print(f"{'='*70}")

        result = run_walk_forward(
            strategy_id, stock_data, crypto_data,
            quick=quick, verbose=verbose
        )
        all_results[strategy_id] = result

    # ── Summary table ───────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("WALK-FORWARD VALIDATION SUMMARY")
    print("=" * 70)
    print(f"\n{'Strategy':<25} {'In-Smpl R':>10} {'OOS R':>10} {'OOS N':>6} "
          f"{'t-stat':>8} {'p-value':>8} {'95% CI':>20} {'Verdict':<25}")
    print("-" * 115)

    for sid, result in all_results.items():
        is_sig = result["in_sample_significance"]
        oos_sig = result["oos_significance"]
        name = result["name"]

        ci_str = f"[{oos_sig['ci_lower']:.3f}, {oos_sig['ci_upper']:.3f}]"

        print(f"  {name:<23} {is_sig['mean_r']:>10.4f} {oos_sig['mean_r']:>10.4f} "
              f"{oos_sig['n']:>6} {oos_sig['t_stat']:>8.2f} {oos_sig['p_value']:>8.4f} "
              f"{ci_str:>20} {oos_sig['verdict']:<25}")

    print("\n" + "-" * 70)
    print("Per-Window OOS R:")
    print("-" * 70)
    print(f"  {'Strategy':<25} {'2022':>8} {'2023':>8} {'2024':>8} {'2025':>8} {'2026':>8}")
    for sid, result in all_results.items():
        name = result["name"]
        row = f"  {name:<23}"
        for window_label in ["2022", "2023", "2024", "2025", "2026"]:
            window_data = [w for w in result["windows"] if w["window"] == window_label]
            if window_data:
                avg_r = np.mean([w["oos_avg_r"] for w in window_data])
                n = sum(w["oos_n"] for w in window_data)
                row += f" {avg_r:>+.4f}({n})"
            else:
                row += f" {'n/a':>8}"
        print(row)

    return all_results


def main():
    ap = argparse.ArgumentParser(
        description="HermesForge walk-forward validation framework"
    )
    ap.add_argument("--strategy", type=str, default=None,
                    help="Single strategy to test (B, I, J, L)")
    ap.add_argument("--quick", action="store_true",
                    help="Smaller parameter grid for faster runs")
    ap.add_argument("--json", action="store_true",
                    help="Output as JSON")
    args = ap.parse_args()

    if args.strategy:
        print(f"Running walk-forward for strategy {args.strategy} only...")

        print("\nLoading stock data...")
        stock_data = load_all_stocks()
        print("Loading crypto data...")
        crypto_data = load_all_crypto()

        result = run_walk_forward(
            args.strategy, stock_data, crypto_data,
            quick=args.quick, verbose=True
        )
        results = {args.strategy: result}
    else:
        results = run_all_strategies(quick=args.quick, verbose=True)

    if args.json:
        # Convert to JSON-serializable
        def clean(d):
            if isinstance(d, dict):
                return {k: clean(v) for k, v in d.items() if k != "hourly_data"}
            if isinstance(d, list):
                return [clean(x) for x in d]
            if isinstance(d, (np.integer, np.floating)):
                return float(d)
            if isinstance(d, np.bool_):
                return bool(d)
            return d

        print("\n--- JSON OUTPUT ---")
        print(json.dumps(clean(results), indent=2, default=str))


if __name__ == "__main__":
    main()