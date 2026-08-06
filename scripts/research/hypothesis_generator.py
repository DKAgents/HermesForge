#!/usr/bin/env python3
"""
hypothesis_generator.py — HermesForge New Strategy Hypothesis Generator

Takes factor screener results and generates new strategy hypotheses by:
  1. Combining top factors (equal-weight and Sharpe-weighted composites)
  2. Testing regime-conditional factor timing
  3. Testing factor interaction (e.g., momentum × low-vol)
  4. Running preliminary backtests for each hypothesis

Each hypothesis is ranked by composite score = Sharpe × (1/p_value) × sign(mean_R).
Top candidates are flagged for full walk-forward validation.

Usage:
    python3 hypothesis_generator.py                    # generate hypotheses
    python3 hypothesis_generator.py --json              # JSON output
    python3 hypothesis_generator.py --crypto            # crypto only
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

from factor_engine import (
    FACTOR_DEFS, QUINTILE, REBALANCE_FREQ,
    COST_PER_TURN, COST_CRYPTO,
    compute_factor_signal, compute_all_factor_signals,
    build_factor_portfolio, analyze_factor_premium,
)
from factor_screener import compute_all_new_factor_signals, NEW_FACTORS

# All factor compute functions unified
ALL_FACTORS = {**FACTOR_DEFS, **NEW_FACTORS}


def _compute_any_factor(data: dict, factor_name: str) -> dict:
    """Compute factor signals for all tickers — handles both existing and new factors."""
    if factor_name in FACTOR_DEFS:
        return compute_all_factor_signals(data, factor_name)
    elif factor_name in NEW_FACTORS:
        return compute_all_new_factor_signals(data, factor_name)
    else:
        return {}


def _build_composite_signals(factor_signals_list: list, weights: list, tickers: set = None) -> dict:
    """
    Combine multiple factor signals into a composite using given weights.
    Each factor signal is z-scored cross-sectionally before combining.

    factor_signals_list: list of {ticker: pd.Series} dicts
    weights: list of floats (same length, sum to 1.0)
    """
    if tickers is None:
        tickers = set()
        for fs in factor_signals_list:
            tickers.update(fs.keys())

    composite = {}
    for ticker in tickers:
        # Get all factor signals for this ticker
        series_list = []
        valid_weights = []
        for i, fs in enumerate(factor_signals_list):
            if ticker in fs:
                series_list.append(fs[ticker])
                valid_weights.append(weights[i])

        if len(series_list) < 2:
            continue

        # Align to common index
        aligned = pd.DataFrame(series_list).T
        aligned.columns = [f"f{i}" for i in range(len(series_list))]

        # Z-score each column (cross-sectional z-score over time)
        for col in aligned.columns:
            mu = aligned[col].rolling(252, min_periods=30).mean()
            sigma = aligned[col].rolling(252, min_periods=30).std()
            aligned[col] = (aligned[col] - mu) / sigma.replace(0, np.nan)

        # Weighted combination
        w_arr = np.array(valid_weights)
        w_arr = w_arr / w_arr.sum()  # normalize
        for i, col in enumerate(aligned.columns):
            aligned[col] = aligned[col] * w_arr[i]

        composite[ticker] = aligned.sum(axis=1)

    return composite


def _test_hypothesis(data: dict, factor_signals: dict, asset_class: str,
                     hypothesis_name: str, description: str) -> dict:
    """Run a preliminary backtest on a factor hypothesis."""
    cost = COST_CRYPTO if asset_class == "crypto" else COST_PER_TURN
    portfolio = build_factor_portfolio(factor_signals, data, cost_per_turn=cost)
    if portfolio.empty:
        return {
            "hypothesis": hypothesis_name,
            "description": description,
            "asset_class": asset_class,
            "error": "portfolio empty",
        }

    result = analyze_factor_premium(portfolio, hypothesis_name, asset_class)

    # Composite score: Sharpe / p_value (higher = better)
    sharpe = result.get("sharpe", 0)
    p_val = max(result.get("p_value", 1), 0.001)
    mean_r = result.get("annualized_return", 0)

    if p_val < 0.05:
        composite_score = abs(sharpe) * (1 / p_val) * np.sign(mean_r)
    elif p_val < 0.10:
        composite_score = abs(sharpe) * 0.5 * np.sign(mean_r)
    else:
        composite_score = 0

    result["hypothesis"] = hypothesis_name
    result["description"] = description
    result["asset_class"] = asset_class
    result["composite_score"] = round(float(composite_score), 3)

    # Flag as candidate if composite_score > 0 AND Sharpe > 0.5
    result["candidate"] = composite_score > 0 and abs(sharpe) > 0.5

    return result


def generate_hypotheses(data: dict, asset_class: str = "stock",
                        top_n: int = 3) -> dict:
    """
    Generate and test new strategy hypotheses based on factor screening.

    1. Compute all factor signals
    2. Test pairwise combinations of top factors
    3. Test equal-weight vs Sharpe-weighted composites
    4. Test single best factor as baseline
    5. Rank all hypotheses by composite score
    """
    # Compute all factor signals
    all_signals = {}
    for fname in ALL_FACTORS:
        sigs = _compute_any_factor(data, fname)
        if sigs:
            all_signals[fname] = sigs
            print(f"  Computed {fname}: {len(sigs)} tickers", file=sys.stderr)

    if len(all_signals) < 2:
        return {
            "asset_class": asset_class,
            "hypotheses": [],
            "candidates": [],
            "note": "Not enough factors with signals to generate hypotheses.",
        }

    # First, compute baseline stats for each factor individually
    factor_baselines = {}
    for fname, sigs in all_signals.items():
        cost = COST_CRYPTO if asset_class == "crypto" else COST_PER_TURN
        portfolio = build_factor_portfolio(sigs, data, cost_per_turn=cost)
        if portfolio.empty:
            continue
        stats = analyze_factor_premium(portfolio, fname, asset_class)
        factor_baselines[fname] = stats
        print(f"  Baseline {fname}: Sharpe={stats.get('sharpe', 0):.3f}, p={stats.get('p_value', 1):.4f}", file=sys.stderr)

    # Rank factors by |Sharpe| for selecting top combinations
    ranked_factors = sorted(
        factor_baselines.items(),
        key=lambda x: abs(x[1].get("sharpe", 0)),
        reverse=True
    )

    if len(ranked_factors) < 2:
        return {
            "asset_class": asset_class,
            "hypotheses": [],
            "candidates": [],
            "note": "Not enough factors with valid baselines to generate hypotheses.",
        }

    # Take top N factors
    top_factors = ranked_factors[:top_n]

    all_hypotheses = []

    # Hypothesis 1: Equal-weight composite of top 2 factors
    if len(top_factors) >= 2:
        f1_name, _ = top_factors[0]
        f2_name, _ = top_factors[1]
        signals_list = [all_signals[f1_name], all_signals[f2_name]]
        weights = [0.5, 0.5]
        composite = _build_composite_signals(signals_list, weights)
        if composite:
            result = _test_hypothesis(
                data, composite, asset_class,
                f"Equal-Weight: {f1_name}+{f2_name}",
                f"50/50 blend of {f1_name} and {f2_name}"
            )
            all_hypotheses.append(result)

    # Hypothesis 2: Equal-weight composite of top 3 factors
    if len(top_factors) >= 3:
        names = [t[0] for t in top_factors[:3]]
        signals_list = [all_signals[n] for n in names]
        weights = [1/3] * 3
        composite = _build_composite_signals(signals_list, weights)
        if composite:
            result = _test_hypothesis(
                data, composite, asset_class,
                f"Equal-Weight: {'+'.join(names)}",
                f"33/33/33 blend of {', '.join(names)}"
            )
            all_hypotheses.append(result)

    # Hypothesis 3: Sharpe-weighted composite of top 3
    if len(top_factors) >= 3:
        names = [t[0] for t in top_factors[:3]]
        sharpes = [abs(factor_baselines[n].get("sharpe", 0.01)) for n in names]
        total_s = sum(sharpes)
        weights = [s / total_s for s in sharpes]
        signals_list = [all_signals[n] for n in names]
        composite = _build_composite_signals(signals_list, weights)
        if composite:
            result = _test_hypothesis(
                data, composite, asset_class,
                f"Sharpe-Weighted: {'+'.join(names)}",
                f"Sharpe-proportional blend of {', '.join(names)}"
            )
            all_hypotheses.append(result)

    # Hypothesis 4: Top factor alone (baseline reference)
    f1_name, f1_stats = top_factors[0]
    result = _test_hypothesis(
        data, all_signals[f1_name], asset_class,
        f"Single: {f1_name}",
        f"Top factor alone (baseline)"
    )
    all_hypotheses.append(result)

    # Hypothesis 5: Momentum × Low-Vol interaction (if both exist)
    mom_factors = [f for f in all_signals if "MOM" in f or "PRICEMOM" in f]
    vol_factors = [f for f in all_signals if "VOL" in f or "ATR" in f or "LOWVOL" in f]
    if mom_factors and vol_factors:
        m_name = mom_factors[0]
        v_name = vol_factors[0]
        signals_list = [all_signals[m_name], all_signals[v_name]]
        weights = [0.6, 0.4]  # momentum-weighted
        composite = _build_composite_signals(signals_list, weights)
        if composite:
            result = _test_hypothesis(
                data, composite, asset_class,
                f"Interaction: {m_name}×{v_name}",
                f"60/40 momentum-volatility interaction"
            )
            all_hypotheses.append(result)

    # Rank by composite score descending
    all_hypotheses.sort(key=lambda x: x.get("composite_score", 0), reverse=True)

    candidates = [h for h in all_hypotheses if h.get("candidate", False)]

    return {
        "asset_class": asset_class,
        "factors_screened": list(all_signals.keys()),
        "top_factors": [t[0] for t in top_factors],
        "hypotheses": all_hypotheses,
        "candidates": candidates,
        "n_hypotheses_tested": len(all_hypotheses),
        "n_candidates": len(candidates),
        "timestamp": datetime.utcnow().isoformat(),
    }


def format_report(stock_results: dict, crypto_results: dict) -> str:
    """Format a human-readable markdown report."""
    lines = []
    lines.append("# HermesForge New Strategy Hypothesis Report")
    lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")

    for results, label in [(stock_results, "Stocks"), (crypto_results, "Crypto")]:
        if not results or not results.get("hypotheses"):
            continue
        lines.append(f"## {label} ({results['n_hypotheses_tested']} hypotheses tested)")
        lines.append(f"Top factors: {', '.join(results.get('top_factors', []))}")
        lines.append("")
        lines.append("| Hypothesis | Sharpe | Annual Ret | p-value | Max DD | Composite | Candidate |")
        lines.append("|------------|--------|------------|---------|--------|-----------|-----------|")
        for h in results["hypotheses"]:
            if "error" in h:
                lines.append(f"| {h['hypothesis']} | — | — | — | — | — | ERROR |")
                continue
            is_cand = "★ YES" if h.get("candidate") else ""
            lines.append(
                f"| {h['hypothesis']} | {h.get('sharpe', 0):.3f} | "
                f"{h.get('annualized_return', 0)*100:.1f}% | "
                f"{h.get('p_value', 1):.4f} | "
                f"{h.get('max_drawdown', 0)*100:.1f}% | "
                f"{h.get('composite_score', 0):.2f} | {is_cand} |"
            )
        lines.append("")
        if results["candidates"]:
            lines.append(f"**{len(results['candidates'])} candidate(s) for full validation:**")
            for c in results["candidates"]:
                lines.append(
                    f"  - **{c['hypothesis']}**: Sharpe {c['sharpe']:.3f}, "
                    f"p={c['p_value']:.4f}, composite score {c['composite_score']:.2f}"
                )
            lines.append("")
            lines.append("_Recommended: Run full walk-forward validation to confirm OOS edge._")
        else:
            lines.append("*No candidates this run. Factor combinations show no significant edge.*")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="New strategy hypothesis generator")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--crypto", action="store_true", help="Crypto only")
    args = parser.parse_args()

    from fetch_data import load_all as load_all_stocks
    from fetch_crypto_data import load_all as load_all_crypto

    stock_results = None
    crypto_results = None

    if not args.crypto:
        print("Loading stock data...", file=sys.stderr)
        stock_data = load_all_stocks()
        print(f"  {len(stock_data)} tickers loaded", file=sys.stderr)
        print("Generating stock hypotheses...", file=sys.stderr)
        stock_results = generate_hypotheses(stock_data, "stock")

    print("Loading crypto data...", file=sys.stderr)
    crypto_data = load_all_crypto()
    print(f"  {len(crypto_data)} tickers loaded", file=sys.stderr)
    print("Generating crypto hypotheses...", file=sys.stderr)
    crypto_results = generate_hypotheses(crypto_data, "crypto")

    if args.json:
        print(json.dumps({"stock": stock_results, "crypto": crypto_results}, indent=2, default=str))
    else:
        print(format_report(stock_results, crypto_results))
