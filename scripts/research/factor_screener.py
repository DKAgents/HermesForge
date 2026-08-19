#!/usr/bin/env python3
"""
factor_screener.py — HermesForge Factor Anomaly Scanner

Scans existing AND new factors across the full stock + crypto universe
to find predictive edges. For each factor, builds a long-short quintile
portfolio, computes Sharpe/t-stat/p-value/max-DD, and ranks by edge strength.

Existing factors tested:
  MOM12_1, REV1, LOWVOL, LIQUID, PRICEMOM  (from factor_engine.py)

New factors tested (computed from OHLCV only, no external data):
  RSI14      — 14-period RSI (mean-reversion: buy oversold, sell overbought)
  BB_WIDTH   — Bollinger Band width percentile (volatility contraction anomaly)
  ATR_PCT    — ATR as % of price (volatility factor: low-vol outperforms)
  VOL_ROC    — Volume rate of change (volume momentum proxy)
  ADX_TREND  — ADX trend strength (trend factor: high ADX = trend persistence)

Output: JSON dict with per-factor stats, ranked by |Sharpe| descending.
Candidate edges flagged: |Sharpe| > 0.5 AND p_value < 0.10.

Usage:
    python3 factor_screener.py                    # scan all factors, print report
    python3 factor_screener.py --json              # JSON output
    python3 factor_screener.py --asset crypto      # crypto only
    python3 factor_screener.py --asset stock       # stocks only
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

# ── New Factor Definitions (computed from OHLCV) ─────────────────────────────

NEW_FACTORS = {
    "RSI14": {
        "description": "14-period RSI (mean-reversion: buy oversold, sell overbought)",
        "direction": "long_low",  # low RSI = oversold = buy
    },
    "BB_WIDTH": {
        "description": "Bollinger Band width percentile (volatility contraction)",
        "direction": "long_low",  # narrow BB = low vol = buy
    },
    "ATR_PCT": {
        "description": "ATR as % of price (low-volatility anomaly)",
        "direction": "long_low",
    },
    "VOL_ROC": {
        "description": "10-bar volume rate of change (volume momentum)",
        "direction": "long_high",
    },
    "ADX_TREND": {
        "description": "ADX trend strength (trend persistence)",
        "direction": "long_high",
    },
}


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _compute_bb_width(df: pd.DataFrame, period: int = 20, num_std: float = 2.0) -> pd.Series:
    sma = df["close"].rolling(period).mean()
    std = df["close"].rolling(period).std()
    upper = sma + num_std * std
    lower = sma - num_std * std
    width = (upper - lower) / sma
    return width


def _compute_atr_pct(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr / close


def _compute_vol_roc(volume: pd.Series, lookback: int = 10) -> pd.Series:
    return volume.pct_change(lookback)


def _compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)
    atr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    atr = atr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1/period, adjust=False).mean()


def compute_new_factor_signal(df: pd.DataFrame, factor_name: str) -> pd.Series:
    """Compute a new factor signal for a single ticker."""
    close = df["close"]
    volume = df["volume"]

    if factor_name == "RSI14":
        signal = _compute_rsi(close, 14)
    elif factor_name == "BB_WIDTH":
        signal = _compute_bb_width(df, 20, 2.0)
    elif factor_name == "ATR_PCT":
        signal = _compute_atr_pct(df, 14)
    elif factor_name == "VOL_ROC":
        signal = _compute_vol_roc(volume, 10)
    elif factor_name == "ADX_TREND":
        signal = _compute_adx(df, 14)
    else:
        return pd.Series(np.nan, index=df.index)

    # Apply direction
    if NEW_FACTORS[factor_name]["direction"] == "long_low":
        signal = -signal
    return signal


def compute_all_new_factor_signals(data: dict, factor_name: str) -> dict:
    """Compute a new factor signal for all tickers."""
    signals = {}
    for ticker, df in data.items():
        if len(df) < 60:
            continue
        sig = compute_new_factor_signal(df, factor_name)
        if not sig.empty:
            signals[ticker] = sig
    return signals


def _safe_analyze(portfolio: pd.DataFrame, factor_name: str, asset_class: str) -> dict:
    """Wrapper around analyze_factor_premium with safe defaults."""
    try:
        result = analyze_factor_premium(portfolio, factor_name, asset_class)
        return result
    except Exception as e:
        return {"factor": factor_name, "asset_class": asset_class, "error": str(e)}


def run_factor_screen(data: dict, asset_class: str = "stock",
                      include_existing: bool = True, include_new: bool = True) -> dict:
    """
    Run full factor screen on a data dict.

    Returns dict with:
      - "asset_class": str
      - "factors": list of result dicts, sorted by |Sharpe| descending
      - "candidates": list of factors flagged as candidate edges
      - "timestamp": ISO timestamp
    """
    cost = COST_CRYPTO if asset_class == "crypto" else COST_PER_TURN
    all_results = []

    # Existing factors
    if include_existing:
        for fname in FACTOR_DEFS:
            signals = compute_all_factor_signals(data, fname)
            if not signals:
                all_results.append({"factor": fname, "asset_class": asset_class, "error": "no signals"})
                continue
            portfolio = build_factor_portfolio(signals, data, cost_per_turn=cost)
            if portfolio.empty:
                all_results.append({"factor": fname, "asset_class": asset_class, "error": "portfolio empty"})
                continue
            all_results.append(_safe_analyze(portfolio, fname, asset_class))

    # New factors
    if include_new:
        for fname in NEW_FACTORS:
            signals = compute_all_new_factor_signals(data, fname)
            if not signals:
                all_results.append({"factor": fname, "asset_class": asset_class, "error": "no signals"})
                continue
            portfolio = build_factor_portfolio(signals, data, cost_per_turn=cost)
            if portfolio.empty:
                all_results.append({"factor": fname, "asset_class": asset_class, "error": "portfolio empty"})
                continue
            all_results.append(_safe_analyze(portfolio, fname, asset_class))

    # Rank by |Sharpe| descending
    ranked = sorted(all_results, key=lambda x: abs(x.get("sharpe", 0)), reverse=True)

    # Flag candidates: |Sharpe| > 0.5 AND p < 0.10
    candidates = [
        r for r in ranked
        if abs(r.get("sharpe", 0)) > 0.5
        and r.get("p_value", 1.0) < 0.10
        and "error" not in r
    ]

    return {
        "asset_class": asset_class,
        "factors": ranked,
        "candidates": candidates,
        "n_factors_tested": len(all_results),
        "n_candidates": len(candidates),
        "timestamp": datetime.utcnow().isoformat(),
    }


def format_report(stock_results: dict, crypto_results: dict) -> str:
    """Format a human-readable markdown report."""
    lines = []
    lines.append("# HermesForge Factor Anomaly Report")
    lines.append(f"Generated: {now_pt().strftime('%Y-%m-%d %H:%M %Z')}")
    lines.append("")

    for results, label in [(stock_results, "Stocks"), (crypto_results, "Crypto")]:
        if not results:
            continue
        lines.append(f"## {label} ({results['n_factors_tested']} factors tested)")
        lines.append("")
        lines.append("| Factor | Sharpe | Annual Ret | p-value | Max DD | Hit Rate | Verdict | Candidate |")
        lines.append("|--------|--------|------------|---------|--------|----------|---------|-----------|")
        for f in results["factors"]:
            if "error" in f:
                lines.append(f"| {f['factor']} | — | — | — | — | — | ERROR: {f['error'][:30]} | — |")
                continue
            is_cand = "★ YES" if f in results["candidates"] else ""
            lines.append(
                f"| {f['factor']} | {f.get('sharpe', 0):.3f} | "
                f"{f.get('annualized_return', 0)*100:.1f}% | "
                f"{f.get('p_value', 1):.4f} | "
                f"{f.get('max_drawdown', 0)*100:.1f}% | "
                f"{f.get('hit_rate', 0)*100:.0f}% | "
                f"{f.get('verdict', '?')} | {is_cand} |"
            )
        lines.append("")
        if results["candidates"]:
            lines.append(f"**{len(results['candidates'])} candidate edge(s) flagged:**")
            for c in results["candidates"]:
                lines.append(
                    f"  - **{c['factor']}**: Sharpe {c['sharpe']:.3f}, "
                    f"p={c['p_value']:.4f}, annual return {c['annualized_return']*100:.1f}%"
                )
            lines.append("")
        else:
            lines.append("*No candidate edges flagged this run.*")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Factor anomaly scanner")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--asset", choices=["stock", "crypto", "both"], default="both")
    args = parser.parse_args()

    from fetch_data import load_all as load_all_stocks
    from fetch_crypto_data import load_all as load_all_crypto

    stock_results = None
    crypto_results = None

    if args.asset in ("stock", "both"):
        print("Loading stock data...", file=sys.stderr)
        stock_data = load_all_stocks()
        print(f"  {len(stock_data)} tickers loaded", file=sys.stderr)
        stock_results = run_factor_screen(stock_data, "stock")

    if args.asset in ("crypto", "both"):
        print("Loading crypto data...", file=sys.stderr)
        crypto_data = load_all_crypto()
        print(f"  {len(crypto_data)} tickers loaded", file=sys.stderr)
        crypto_results = run_factor_screen(crypto_data, "crypto")

    if args.json:
        output = {"stock": stock_results, "crypto": crypto_results}
        print(json.dumps(output, indent=2, default=str))
    else:
        print(format_report(stock_results, crypto_results))
