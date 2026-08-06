#!/usr/bin/env python3
"""
decay_monitor.py — HermesForge Strategy Edge Decay Monitor

Tracks whether LIVE and WATCH strategies' edges are eroding over time.
Runs a lightweight walk-forward on the most recent OOS window and compares
to historical snapshots stored in a JSON file.

Monitored strategies:
  STR-B (MACD Divergence) — LIVE (stocks)
  STR-I (Adaptive Trend) — LIVE (stocks)
  STR-P (Cross-Sectional Factor) — WATCH (crypto)
  STR-L (ATR Contraction) — WATCH (stocks)

For each: runs walk-forward latest OOS window, computes mean R, Sharpe, p-value.
Compares to prior snapshots stored in decay_history.json.
Flags if: Sharpe dropped > 30% from first recorded snapshot.

Usage:
    python3 decay_monitor.py                     # run decay check
    python3 decay_monitor.py --json               # JSON output
    python3 decay_monitor.py --history            # show full trend
"""

import sys
import json
import argparse
import pathlib
import numpy as np
import pandas as pd
from datetime import datetime
from statistics import NormalDist

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation" / "scanners"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))

from walk_forward import (
    STRATEGY_CONFIGS, QUICK_PARAMS, OPTIMIZATION_SAMPLE, CRYPTO_OPTIMIZATION_SAMPLE,
    scan_with_params, apply_costs, apply_gap_risk, compute_significance,
)

# ── Monitored Strategies ────────────────────────────────────────────────────

MONITORED = {
    "B": {"module": "scanner_b_macd_divergence", "scan_fn": "scan", "name": "MACD Divergence",
          "status": "LIVE", "asset_class": "stock", "call_mode": "per_ticker", "long_only": True},
    "I": {"module": "scanner_i_adaptive_trend", "scan_fn": "scan", "name": "Adaptive Trend",
          "status": "LIVE", "asset_class": "stock", "call_mode": "per_ticker", "long_only": True},
    "P": {"module": "scanner_p_crosssectional", "scan_fn": "scan", "name": "Cross-Sectional Factor",
          "status": "WATCH", "asset_class": "crypto", "call_mode": "batch", "long_only": False},
    "L": {"module": "scanner_l_atr_contraction", "scan_fn": "scan_ticker", "name": "ATR Contraction",
          "status": "WATCH", "asset_class": "stock", "call_mode": "per_ticker", "long_only": True},
}

# Decay history file
HISTORY_FILE = REPO_ROOT / "data" / "decay_history.json"

# OOS window: most recent 2 years
OOS_START = "2024-01-01"
OOS_END = "2026-12-31"

# Decay threshold: 30% Sharpe drop from first snapshot
DECAY_THRESHOLD = 0.30


def _load_history() -> dict:
    """Load decay history from JSON file."""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {}


def _save_history(history: dict):
    """Save decay history to JSON file."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2, default=str)


def _run_strategy(strategy_key: str, stock_data: dict, crypto_data: dict) -> dict:
    """Run a single strategy on recent OOS data and return stats."""
    config = MONITORED[strategy_key]
    asset_class = config["asset_class"]
    call_mode = config["call_mode"]
    long_only = config["long_only"]

    # Get parameter grid (use quick params for speed)
    quick_key = strategy_key
    if quick_key in QUICK_PARAMS:
        params = QUICK_PARAMS[quick_key]
    elif strategy_key in STRATEGY_CONFIGS:
        params = STRATEGY_CONFIGS[strategy_key]["params"]
    else:
        params = {}

    # Use default params (first value from each grid)
    default_params = {k: v[0] for k, v in params.items()} if params else {}

    # Import module
    import importlib
    module = importlib.import_module(config["module"])

    # Select data
    data = crypto_data if asset_class == "crypto" else stock_data

    # Sample tickers
    if asset_class == "crypto":
        sample = CRYPTO_OPTIMIZATION_SAMPLE
    else:
        sample = OPTIMIZATION_SAMPLE

    all_signals = []

    if call_mode == "per_ticker":
        for ticker in sample:
            if ticker not in data:
                continue
            df = data[ticker]
            recent = df[df.index >= pd.Timestamp(OOS_START)]
            if len(recent) < 30:
                continue
            try:
                signals = scan_with_params(
                    module, config["scan_fn"], {ticker: recent},
                    default_params, OOS_START, OOS_END,
                    asset_class=asset_class, long_only=long_only,
                    apply_cost=True, call_mode="per_ticker"
                )
                all_signals.extend(signals)
            except Exception:
                continue
    elif call_mode == "batch":
        # Batch scanner (STR-P) — use default params directly
        for key, val in default_params.items():
            if hasattr(module, key):
                setattr(module, key, val)
        try:
            # Filter data to recent
            recent_data = {}
            for ticker, df in data.items():
                recent = df[df.index >= pd.Timestamp(OOS_START)]
                if len(recent) >= 60:
                    recent_data[ticker] = recent
            signals = module.scan(recent_data)
            if signals:
                all_signals.extend(signals)
        except Exception as e:
            return {"strategy": f"STR-{strategy_key}", "error": f"batch scan failed: {e}"}

    if not all_signals:
        return {
            "strategy": f"STR-{strategy_key}",
            "name": config["name"],
            "status": config["status"],
            "n_signals": 0,
            "mean_r": 0,
            "sharpe_proxy": 0,
            "p_value": 1.0,
            "verdict": "NO SIGNALS",
            "decay_flag": False,
            "note": "No signals in OOS window",
        }

    # Compute stats
    r_values = [float(s.get("r_multiple", 0)) for s in all_signals if s.get("r_multiple") is not None]
    stats = compute_significance(r_values)

    # Sharpe proxy: mean_r / std_r * sqrt(n) — annualized approximation
    if stats["std_r"] > 0 and stats["n"] > 0:
        sharpe_proxy = stats["mean_r"] / stats["std_r"] * np.sqrt(252 / 21)  # ~monthly R annualized
    else:
        sharpe_proxy = 0

    # Hit rate
    hits = sum(1 for r in r_values if r > 0)
    hit_rate = hits / len(r_values) if r_values else 0

    return {
        "strategy": f"STR-{strategy_key}",
        "name": config["name"],
        "status": config["status"],
        "n_signals": stats["n"],
        "mean_r": stats["mean_r"],
        "std_r": stats["std_r"],
        "sharpe_proxy": round(float(sharpe_proxy), 3),
        "p_value": stats["p_value"],
        "ci_lower": stats["ci_lower"],
        "ci_upper": stats["ci_upper"],
        "hit_rate": round(hit_rate, 3),
        "verdict": stats["verdict"],
    }


def run_decay_check(stock_data: dict, crypto_data: dict) -> dict:
    """
    Run decay check on all monitored strategies.
    Compares to history and flags decay.
    """
    history = _load_history()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    results = []
    for key in MONITORED:
        print(f"  Testing STR-{key} ({MONITORED[key]['name']})...", file=sys.stderr)
        result = _run_strategy(key, stock_data, crypto_data)
        if "error" in result:
            results.append(result)
            continue

        strat_id = f"STR-{key}"

        # Get prior snapshots
        prior_snapshots = history.get(strat_id, [])

        if prior_snapshots:
            first = prior_snapshots[0]
            first_sharpe = first.get("sharpe_proxy", 0)
            current_sharpe = result["sharpe_proxy"]

            if first_sharpe > 0:
                decay_pct = (first_sharpe - current_sharpe) / abs(first_sharpe)
            elif first_sharpe < 0:
                decay_pct = 0  # Was negative, still negative
            else:
                decay_pct = 0

            result["first_sharpe"] = first_sharpe
            result["decay_pct"] = round(float(decay_pct), 3)
            result["decay_flag"] = decay_pct > DECAY_THRESHOLD
            result["snapshots_count"] = len(prior_snapshots)

            if result["decay_flag"]:
                result["note"] = f"DECAY DETECTED: Sharpe dropped {decay_pct*100:.0f}% from initial"
            else:
                result["note"] = f"Stable: Sharpe change {decay_pct*100:+.0f}% vs initial"
        else:
            result["first_sharpe"] = result["sharpe_proxy"]
            result["decay_pct"] = 0
            result["decay_flag"] = False
            result["snapshots_count"] = 0
            result["note"] = "First snapshot — baseline established"

        # Save snapshot
        snapshot = {
            "date": today,
            "n_signals": result["n_signals"],
            "mean_r": result["mean_r"],
            "sharpe_proxy": result["sharpe_proxy"],
            "p_value": result["p_value"],
            "hit_rate": result.get("hit_rate", 0),
            "verdict": result["verdict"],
        }
        prior_snapshots.append(snapshot)
        history[strat_id] = prior_snapshots

        results.append(result)

    # Save updated history
    _save_history(history)

    # Sort: decayed first
    results.sort(key=lambda x: x.get("decay_pct", 0), reverse=True)

    decayed = [r for r in results if r.get("decay_flag", False)]

    return {
        "strategies_monitored": len(results),
        "n_decayed": len(decayed),
        "results": results,
        "decayed": decayed,
        "timestamp": datetime.utcnow().isoformat(),
    }


def format_report(results: dict, show_history: bool = False) -> str:
    """Format a human-readable markdown report."""
    lines = []
    lines.append("# HermesForge Strategy Edge Decay Report")
    lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"Strategies monitored: {results['strategies_monitored']}")
    lines.append(f"Decay flags: {results['n_decayed']}")
    lines.append("")
    lines.append("| Strategy | Name | Status | N Sig | Mean R | Sharpe | p-value | Decay % | Flag |")
    lines.append("|----------|------|--------|-------|--------|--------|---------|---------|------|")
    for r in results["results"]:
        if "error" in r:
            lines.append(f"| {r['strategy']} | {r.get('name','')} | — | — | — | — | — | — | ERROR |")
            continue
        flag = "⚠️ DECAY" if r.get("decay_flag") else "✓ OK"
        decay_str = f"{r.get('decay_pct', 0)*100:+.0f}%" if "decay_pct" in r else "—"
        lines.append(
            f"| {r['strategy']} | {r['name']} | {r['status']} | "
            f"{r.get('n_signals', 0)} | {r.get('mean_r', 0):.4f} | "
            f"{r.get('sharpe_proxy', 0):.3f} | {r.get('p_value', 1):.4f} | "
            f"{decay_str} | {flag} |"
        )
    lines.append("")

    if results["decayed"]:
        lines.append(f"**{len(results['decayed'])} strategy(ies) showing edge decay:**")
        for d in results["decayed"]:
            lines.append(
                f"  - **{d['strategy']} ({d['name']})**: Sharpe dropped from "
                f"{d.get('first_sharpe', 0):.3f} to {d.get('sharpe_proxy', 0):.3f} "
                f"({d.get('decay_pct', 0)*100:.0f}% decline)"
            )
        lines.append("")
        lines.append("_Recommended action: Re-run full walk-forward validation to confirm decay._")
    else:
        lines.append("*All strategies stable. No edge decay detected.*")

    if show_history:
        history = _load_history()
        lines.append("")
        lines.append("## Historical Snapshots")
        for strat_id, snapshots in history.items():
            lines.append(f"### {strat_id}")
            lines.append("| Date | N Sig | Mean R | Sharpe | p-value | Verdict |")
            lines.append("|------|-------|--------|--------|---------|---------|")
            for s in snapshots[-5:]:  # last 5 snapshots
                lines.append(
                    f"| {s['date']} | {s['n_signals']} | {s['mean_r']:.4f} | "
                    f"{s['sharpe_proxy']:.3f} | {s['p_value']:.4f} | {s['verdict']} |"
                )
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strategy edge decay monitor")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--history", action="store_true", help="Show full history")
    args = parser.parse_args()

    from fetch_data import load_all as load_all_stocks
    from fetch_crypto_data import load_all as load_all_crypto

    print("Loading stock data...", file=sys.stderr)
    stock_data = load_all_stocks()
    print(f"  {len(stock_data)} tickers loaded", file=sys.stderr)
    print("Loading crypto data...", file=sys.stderr)
    crypto_data = load_all_crypto()
    print(f"  {len(crypto_data)} tickers loaded", file=sys.stderr)

    results = run_decay_check(stock_data, crypto_data)

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print(format_report(results, show_history=args.history))
