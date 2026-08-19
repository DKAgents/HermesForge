#!/usr/bin/env python3
"""
revival_tester.py — HermesForge Killed Strategy Revival Tester

Re-tests KILLED strategies against the most recent data to check if
regime changes have made any of them viable again. This is a lightweight
version of full walk-forward — just runs the latest OOS window.

KILLED strategies tested (12):
  STR-A (MA Pullback), STR-C (Breakout Volume), STR-D (S/R Role Reversal),
  STR-E (RSI Mean Reversion), STR-F (Bollinger Squeeze),
  STR-G (Relative Strength Rotation), STR-H (First Pullback Trend Swing),
  STR-J (EUFEARIA CCI), STR-K (Breadth Gap), STR-M (Selling Climax),
  STR-N (Outside Day Key Reversal), STR-O (Price Momentum)

For each: runs scanner with default params, computes mean R, p-value, hit rate.
Flags for potential revival if: mean R > 0 AND p_value < 0.15.

Usage:
    python3 revival_tester.py                    # test all killed strategies
    python3 revival_tester.py --json              # JSON output
    python3 revival_tester.py --strategy E        # single strategy
"""

import sys
import json
import argparse
import pathlib
import importlib
import numpy as np
import pandas as pd
from datetime import datetime
from statistics import NormalDist

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation" / "scanners"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))

from walk_forward import apply_costs, compute_significance, OPTIMIZATION_SAMPLE

# ── KILLED Strategy Registry ─────────────────────────────────────────────────
# Each entry: module name, scan function, call mode, asset class support

KILLED_STRATEGIES = {
    "A": {
        "module": "scanner_a_ma_pullback",
        "scan_fn": "scan",
        "name": "MA Pullback",
        "call_mode": "per_ticker",
        "asset_class": "stock",
    },
    "C": {
        "module": "scanner_c_breakout_volume",
        "scan_fn": "scan",
        "name": "Breakout Volume",
        "call_mode": "per_ticker",
        "asset_class": "stock",
    },
    "D": {
        "module": "scanner_d_sr_reversal",
        "scan_fn": "scan",
        "name": "S/R Role Reversal",
        "call_mode": "per_ticker",
        "asset_class": "stock",
    },
    "E": {
        "module": "scanner_e_rsi_mean_reversion",
        "scan_fn": "scan",
        "name": "RSI Mean Reversion",
        "call_mode": "per_ticker",
        "asset_class": "stock",
    },
    "F": {
        "module": "scanner_f_bollinger_squeeze",
        "scan_fn": "scan",
        "name": "Bollinger Squeeze Breakout",
        "call_mode": "per_ticker",
        "asset_class": "stock",
    },
    "G": {
        "module": "scanner_g_relative_strength",
        "scan_fn": "scan",
        "name": "Relative Strength Rotation",
        "call_mode": "per_ticker",
        "asset_class": "stock",
    },
    "H": {
        "module": "scanner_h_first_pullback_trend_swing",
        "scan_fn": "scan",
        "name": "First Pullback Trend Swing",
        "call_mode": "per_ticker",
        "asset_class": "stock",
    },
    "J": {
        "module": "scanner_j_eufearia_cci",
        "scan_fn": "scan",
        "name": "EUFEARIA CCI",
        "call_mode": "per_ticker",
        "asset_class": "stock",
    },
    "K": {
        "module": "scanner_k_breadth_gap",
        "scan_fn": "scan",
        "name": "Breadth Gap Reversal",
        "call_mode": "batch",
        "asset_class": "stock",
    },
    "M": {
        "module": "scanner_m_selling_climax",
        "scan_fn": "scan",
        "name": "Selling Climax Reversal",
        "call_mode": "batch",
        "asset_class": "stock",
    },
    "N": {
        "module": "scanner_n_outside_day",
        "scan_fn": "scan",
        "name": "Outside Day Key Reversal",
        "call_mode": "batch",
        "asset_class": "stock",
    },
    "O": {
        "module": "scanner_o_pricemom",
        "scan_fn": "scan",
        "name": "Price Momentum",
        "call_mode": "per_ticker",
        "asset_class": "stock",
    },
}

# Sample of 30 liquid tickers for testing (from walk_forward.py)
TEST_SAMPLE = OPTIMIZATION_SAMPLE

# Only test 2024-2026 data (most recent ~2 years)
OOS_START = "2024-01-01"


def test_revival(strategy_key: str, stock_data: dict, crypto_data: dict = None) -> dict:
    """
    Test a single killed strategy on recent data.
    Returns dict with stats and revival flag.
    """
    config = KILLED_STRATEGIES[strategy_key]
    module_name = config["module"]
    scan_fn_name = config["scan_fn"]
    call_mode = config["call_mode"]
    asset_class = config["asset_class"]

    # Import the scanner module
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        return {
            "strategy": f"STR-{strategy_key}",
            "name": config["name"],
            "error": f"import failed: {e}",
        }

    scan_fn = getattr(module, scan_fn_name, None)
    if scan_fn is None:
        return {
            "strategy": f"STR-{strategy_key}",
            "name": config["name"],
            "error": f"scan function '{scan_fn_name}' not found",
        }

    all_signals = []

    if call_mode == "per_ticker":
        # Test on a sample of liquid stocks
        for ticker in TEST_SAMPLE:
            if ticker not in stock_data:
                continue
            df = stock_data[ticker]
            # Filter to recent data
            recent = df[df.index >= pd.Timestamp(OOS_START)]
            if len(recent) < 30:
                continue
            try:
                signals = scan_fn(recent, ticker)
                if signals:
                    all_signals.extend(signals)
            except Exception as e:
                # Skip tickers that error
                continue
    elif call_mode == "batch":
        # Batch scanners take the full data dict
        # Filter data to recent dates
        recent_data = {}
        for ticker, df in stock_data.items():
            recent = df[df.index >= pd.Timestamp(OOS_START)]
            if len(recent) >= 30:
                recent_data[ticker] = recent
        try:
            signals = scan_fn(recent_data)
            if signals:
                all_signals.extend(signals)
        except Exception as e:
            return {
                "strategy": f"STR-{strategy_key}",
                "name": config["name"],
                "error": f"batch scan failed: {e}",
            }

    if not all_signals:
        return {
            "strategy": f"STR-{strategy_key}",
            "name": config["name"],
            "n_signals": 0,
            "mean_r": 0,
            "p_value": 1.0,
            "verdict": "NO SIGNALS",
            "revival_candidate": False,
            "note": "Strategy produced 0 signals in recent data.",
        }

    # Apply transaction costs
    for sig in all_signals:
        sig = apply_costs(sig, asset_class="stock")

    # Compute significance
    r_values = [float(s.get("r_multiple", 0)) for s in all_signals if s.get("r_multiple") is not None]
    stats = compute_significance(r_values)

    # Hit rate
    hits = sum(1 for r in r_values if r > 0)
    hit_rate = hits / len(r_values) if r_values else 0

    # Revival flag: mean R > 0 AND p < 0.15
    revival = stats["mean_r"] > 0 and stats["p_value"] < 0.15

    return {
        "strategy": f"STR-{strategy_key}",
        "name": config["name"],
        "n_signals": stats["n"],
        "mean_r": stats["mean_r"],
        "std_r": stats["std_r"],
        "t_stat": stats["t_stat"],
        "p_value": stats["p_value"],
        "ci_lower": stats["ci_lower"],
        "ci_upper": stats["ci_upper"],
        "hit_rate": round(hit_rate, 3),
        "verdict": stats["verdict"],
        "revival_candidate": revival,
        "note": "FLAGGED FOR REVIVAL" if revival else "Still no edge",
    }


def run_revival_tests(stock_data: dict, crypto_data: dict = None,
                      strategies: list = None) -> dict:
    """
    Run revival tests on all (or specified) killed strategies.
    Returns structured results dict.
    """
    if strategies is None:
        strategies = list(KILLED_STRATEGIES.keys())

    results = []
    for key in strategies:
        print(f"  Testing STR-{key} ({KILLED_STRATEGIES[key]['name']})...", file=sys.stderr)
        result = test_revival(key, stock_data, crypto_data)
        results.append(result)

    # Sort: revival candidates first, then by mean R descending
    results.sort(key=lambda x: (x.get("revival_candidate", False), x.get("mean_r", 0)), reverse=True)

    candidates = [r for r in results if r.get("revival_candidate", False)]

    return {
        "strategies_tested": len(results),
        "n_candidates": len(candidates),
        "results": results,
        "candidates": candidates,
        "timestamp": datetime.utcnow().isoformat(),
    }


def format_report(results: dict) -> str:
    """Format a human-readable markdown report."""
    lines = []
    lines.append("# HermesForge Killed Strategy Revival Report")
    lines.append(f"Generated: {now_pt().strftime('%Y-%m-%d %H:%M %Z')}")
    lines.append(f"Strategies tested: {results['strategies_tested']}")
    lines.append(f"Revival candidates: {results['n_candidates']}")
    lines.append("")
    lines.append("| Strategy | Name | N Signals | Mean R | p-value | Hit Rate | Verdict | Revival? |")
    lines.append("|----------|------|-----------|--------|---------|----------|---------|----------|")
    for r in results["results"]:
        if "error" in r:
            lines.append(f"| {r['strategy']} | {r['name']} | — | — | — | — | ERROR | — |")
            continue
        revival = "★ YES" if r.get("revival_candidate") else "No"
        lines.append(
            f"| {r['strategy']} | {r['name']} | {r.get('n_signals', 0)} | "
            f"{r.get('mean_r', 0):.4f} | {r.get('p_value', 1):.4f} | "
            f"{r.get('hit_rate', 0)*100:.0f}% | {r.get('verdict', '?')} | {revival} |"
        )
    lines.append("")
    if results["candidates"]:
        lines.append(f"**{len(results['candidates'])} revival candidate(s):**")
        for c in results["candidates"]:
            lines.append(
                f"  - **{c['strategy']} ({c['name']})**: Mean R={c['mean_r']:.4f}, "
                f"p={c['p_value']:.4f}, {c.get('n_signals', 0)} signals"
            )
        lines.append("")
        lines.append("_Recommended action: Re-run full walk-forward validation to confirm._")
    else:
        lines.append("*No revival candidates this run. All killed strategies remain dead.*")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Killed strategy revival tester")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--strategy", type=str, default=None, help="Single strategy letter (e.g. E)")
    args = parser.parse_args()

    from fetch_data import load_all as load_all_stocks

    print("Loading stock data...", file=sys.stderr)
    stock_data = load_all_stocks()
    print(f"  {len(stock_data)} tickers loaded", file=sys.stderr)

    strategies = [args.strategy.upper()] if args.strategy else None
    results = run_revival_tests(stock_data, strategies=strategies)

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print(format_report(results))
