#!/usr/bin/env python3
"""
factor_engine.py — HermesForge Factor Construction & Decomposition

Part 1: Constructs classic factor premia from our existing data (free, no
        external data needed). For each date, ranks all tickers by a factor
        signal, forms a long-top-quintile / short-bottom-quintile portfolio,
        and tracks the factor return over time.

Part 2: Decomposes our existing strategy returns onto factor exposures.
        For each STR-B/STR-I signal, records the factor rank at entry and
        runs a regression of signal R onto factor exposures. This tells us
        whether our strategy edge is actually a momentum bet, a low-vol
        bet, or something else entirely.

Factors constructed (all using only OHLCV we already have):
  - MOM12_1:  12-month momentum minus most recent month (classic Jegadeesh-Titman)
  - REV1:     1-month reversal (short-term mean reversion)
  - LOWVOL:   60-day realized volatility (low-vol anomaly)
  - LIQUID:   Average dollar volume (liquidity factor)
  - SIZE:     Market cap proxy (price × shares outstanding ~ price × volume)
  - PRICEMOM: Price level relative to 200-day SMA (trend factor)
  - CARRY:    Roll yield proxy for crypto (front-month vs further out)

Usage:
    python3 factor_engine.py                    # compute all factors, print summary
    python3 factor_engine.py --json             # JSON output
    python3 factor_engine.py --decompose        # decompose STR-B and STR-I
    python3 factor_engine.py --factor MOM12_1   # single factor detail
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
sys.path.insert(0, str(REPO_ROOT / "scripts" / "discord"))

from fetch_data import load_all as load_all_stocks
from fetch_crypto_data import load_all as load_all_crypto
from scanner_b_macd_divergence import scan as scan_b
from scanner_i_adaptive_trend import scan as scan_i

# ── Configuration ─────────────────────────────────────────────────────────────

FACTOR_DEFS = {
    "MOM12_1": {
        "description": "12-month momentum excluding most recent month (Jegadeesh-Titman)",
        "lookback": 252,   # 12 months
        "skip": 21,        # skip most recent month
        "direction": "long_high",  # high rank = high momentum
    },
    "REV1": {
        "description": "1-month short-term reversal",
        "lookback": 21,
        "skip": 0,
        "direction": "long_low",   # low rank = recent loser → buy
    },
    "LOWVOL": {
        "description": "60-day realized volatility (low-vol anomaly: low vol outperforms)",
        "lookback": 60,
        "skip": 0,
        "direction": "long_low",   # low rank = low volatility → buy
    },
    "LIQUID": {
        "description": "Average dollar volume (liquidity factor)",
        "lookback": 60,
        "skip": 0,
        "direction": "long_high",  # high rank = more liquid
    },
    "PRICEMOM": {
        "description": "Price relative to 200-day SMA (trend factor)",
        "lookback": 200,
        "skip": 0,
        "direction": "long_high",
    },
}

QUINTILE = 5  # top/bottom quintile for long-short portfolios
REBALANCE_FREQ = 21  # rebalance monthly (21 trading days)
COST_PER_TURN = 0.0012  # 12bp round-trip cost (stocks)
COST_CRYPTO = 0.0005    # 5bp round-trip cost (crypto)
BOOTSTRAP_SAMPLES = 5000


# ── Part 1: Factor Signal Computation ─────────────────────────────────────────

def compute_factor_signal(df: pd.DataFrame, factor_name: str) -> pd.Series:
    """
    Compute a factor signal for a single ticker over time.
    Returns a Series indexed by date with the factor value.

    Higher value = stronger signal in the "buy" direction (after direction adjustment).
    """
    config = FACTOR_DEFS[factor_name]
    close = df["close"]
    volume = df["volume"]
    high = df["high"]
    low = df["low"]

    lookback = config["lookback"]
    skip = config["skip"]
    direction = config["direction"]

    if factor_name == "MOM12_1":
        # 12-month return minus most recent month
        signal = close.shift(skip) / close.shift(lookback + skip) - 1
    elif factor_name == "REV1":
        # 1-month return (inverted — buy losers)
        signal = close / close.shift(lookback) - 1
    elif factor_name == "LOWVOL":
        # 60-day realized volatility of daily returns
        ret = close.pct_change()
        signal = ret.rolling(window=lookback).std() * np.sqrt(252)
    elif factor_name == "LIQUID":
        # Average dollar volume over 60 days
        dollar_vol = close * volume
        signal = dollar_vol.rolling(window=lookback).mean()
    elif factor_name == "PRICEMOM":
        # Price relative to 200-day SMA
        sma = close.rolling(window=lookback).mean()
        signal = close / sma - 1
    else:
        signal = pd.Series(np.nan, index=df.index)

    # Adjust direction: "long_low" means we invert (low value = strong buy signal)
    if direction == "long_low":
        signal = -signal

    return signal


def compute_all_factor_signals(data: dict, factor_name: str) -> dict:
    """
    Compute factor signal for all tickers in data dict.
    Returns {ticker: pd.Series} mapping.
    """
    signals = {}
    for ticker, df in data.items():
        if len(df) < 260:
            continue
        sig = compute_factor_signal(df, factor_name)
        if not sig.empty:
            signals[ticker] = sig
    return signals


# ── Part 2: Factor Portfolio Construction ────────────────────────────────────

def build_factor_portfolio(factor_signals: dict, data: dict,
                            rebalance_freq: int = REBALANCE_FREQ,
                            cost_per_turn: float = COST_PER_TURN,
                            start_date: str = "2019-06-01") -> pd.DataFrame:
    """
    Build a long-short factor portfolio.

    At each rebalance date:
      1. Rank all tickers by factor signal
      2. Long the top quintile, short the bottom quintile (equal weight)
      3. Hold until next rebalance
      4. Compute daily returns of the long-short portfolio
      5. Apply transaction costs on each turnover

    Returns DataFrame with columns: date, long_ret, short_ret, ls_ret, cost, net_ret
    """
    # Get all unique dates
    all_dates = set()
    for sig in factor_signals.values():
        all_dates.update(sig.index)
    all_dates = sorted(all_dates)

    # Filter to start date
    all_dates = [d for d in all_dates if d >= pd.Timestamp(start_date)]

    if len(all_dates) < 60:
        return pd.DataFrame()

    # Rebalance dates (every N trading days)
    rebalance_dates = all_dates[::rebalance_freq]

    # Compute daily returns for each ticker
    returns = {}
    for ticker, df in data.items():
        if ticker not in factor_signals:
            continue
        ret = df["close"].pct_change()
        returns[ticker] = ret

    # Build portfolio returns
    portfolio_rows = []
    current_long = set()
    current_short = set()

    for date in all_dates:
        # Check if this is a rebalance date
        if date in rebalance_dates:
            # Get factor values at this date for all tickers
            tickers_with_signal = []
            for ticker, sig in factor_signals.items():
                if date in sig.index and not pd.isna(sig.loc[date]):
                    tickers_with_signal.append((ticker, sig.loc[date]))

            if len(tickers_with_signal) < QUINTILE:
                continue

            # Sort by factor signal (descending — high = strong buy)
            tickers_with_signal.sort(key=lambda x: x[1], reverse=True)
            n = len(tickers_with_signal)
            quintile_size = n // QUINTILE

            new_long = set(t for t, _ in tickers_with_signal[:quintile_size])
            new_short = set(t for t, _ in tickers_with_signal[-quintile_size:])

            # Compute turnover for cost
            turnover = len(new_long - current_long) + len(new_short - current_short)
            turnover_pct = turnover / max(len(new_long) + len(new_short), 1)
            cost = turnover_pct * cost_per_turn

            current_long = new_long
            current_short = new_short
        else:
            cost = 0.0

        # Compute portfolio return for this date
        long_rets = []
        short_rets = []
        for ticker in current_long:
            if ticker in returns and date in returns[ticker].index:
                r = returns[ticker].loc[date]
                if not pd.isna(r):
                    long_rets.append(r)
        for ticker in current_short:
            if ticker in returns and date in returns[ticker].index:
                r = returns[ticker].loc[date]
                if not pd.isna(r):
                    short_rets.append(r)

        if not long_rets or not short_rets:
            continue

        long_ret = np.mean(long_rets)
        short_ret = np.mean(short_rets)
        ls_ret = long_ret - short_ret
        net_ret = ls_ret - cost

        portfolio_rows.append({
            "date": date,
            "long_ret": long_ret,
            "short_ret": short_ret,
            "ls_ret": ls_ret,
            "cost": cost,
            "net_ret": net_ret,
            "n_long": len(long_rets),
            "n_short": len(short_rets),
        })

    return pd.DataFrame(portfolio_rows).set_index("date")


# ── Part 3: Factor Premia Analysis ─────────────────────────────────────────────

def analyze_factor_premium(portfolio: pd.DataFrame, factor_name: str,
                           asset_class: str = "stock") -> dict:
    """
    Analyze the factor premium: cumulative return, Sharpe ratio,
    significance test, annualized return, max drawdown.
    """
    if portfolio.empty:
        return {"factor": factor_name, "error": "no data"}

    daily_rets = portfolio["net_ret"]

    # Annualized return (252 trading days)
    annual_ret = daily_rets.mean() * 252
    annual_vol = daily_rets.std() * np.sqrt(252)
    sharpe = annual_ret / annual_vol if annual_vol > 0 else 0

    # Cumulative return
    cum_ret = (1 + daily_rets).cumprod().iloc[-1] - 1

    # Max drawdown
    cum = (1 + daily_rets).cumprod()
    running_max = cum.expanding().max()
    drawdown = (cum - running_max) / running_max
    max_dd = drawdown.min()

    # Significance test: t-test on daily returns (H0: mean = 0)
    n = len(daily_rets)
    mean_r = daily_rets.mean()
    std_r = daily_rets.std()
    t_stat = mean_r / (std_r / np.sqrt(n)) if std_r > 0 else 0
    p_value = 2 * (1 - NormalDist(0, 1).cdf(abs(t_stat))) if abs(t_stat) < 100 else 0.0

    # Bootstrap CI on daily returns
    bootstrap_means = []
    for _ in range(BOOTSTRAP_SAMPLES):
        sample = np.random.choice(daily_rets.values, size=n, replace=True)
        bootstrap_means.append(np.mean(sample))

    ci_lower = np.percentile(bootstrap_means, 2.5) * 252  # annualized
    ci_upper = np.percentile(bootstrap_means, 97.5) * 252

    # Hit rate
    hit_rate = (daily_rets > 0).mean()

    return {
        "factor": factor_name,
        "asset_class": asset_class,
        "n_days": n,
        "annualized_return": round(annual_ret, 4),
        "annualized_vol": round(annual_vol, 4),
        "sharpe": round(sharpe, 3),
        "cumulative_return": round(cum_ret, 4),
        "max_drawdown": round(max_dd, 4),
        "hit_rate": round(hit_rate, 3),
        "t_stat": round(t_stat, 3),
        "p_value": round(p_value, 4),
        "ci_lower_annualized": round(ci_lower, 4),
        "ci_upper_annualized": round(ci_upper, 4),
        "significant": p_value < 0.05,
        "verdict": "ROBUST" if p_value < 0.01 else ("SIGNIFICANT" if p_value < 0.05 else "NOT SIGNIFICANT"),
    }


def run_factor_analysis(data: dict, asset_class: str = "stock",
                         factors: list = None, verbose: bool = True) -> dict:
    """
    Run full factor analysis for an asset class.
    """
    if factors is None:
        factors = list(FACTOR_DEFS.keys())

    cost = COST_CRYPTO if asset_class == "crypto" else COST_PER_TURN

    results = {}
    for factor_name in factors:
        if verbose:
            print(f"  Computing {factor_name} ({asset_class})...")

        signals = compute_all_factor_signals(data, factor_name)
        if not signals:
            results[factor_name] = {"error": "no signals computed"}
            continue

        portfolio = build_factor_portfolio(signals, data, cost_per_turn=cost)
        if portfolio.empty:
            results[factor_name] = {"error": "portfolio empty"}
            continue

        analysis = analyze_factor_premium(portfolio, factor_name, asset_class)
        results[factor_name] = analysis

        if verbose:
            ann = analysis.get("annualized_return", 0)
            sharpe = analysis.get("sharpe", 0)
            sig = analysis.get("verdict", "?")
            p = analysis.get("p_value", 1)
            print(f"    Annualized return: {ann:+.2%} | Sharpe: {sharpe:.2f} | "
                  f"p={p:.4f} | {sig}")

    return results


# ── Part 4: Strategy Return Decomposition ─────────────────────────────────────

def decompose_strategy_returns(strategy_id: str, scan_fn, data: dict,
                                asset_class: str = "stock",
                                long_only: bool = False,
                                verbose: bool = True) -> dict:
    """
    For each signal from a strategy, record the factor exposures at entry.

    Then regress: R = alpha + beta_1 * MOM12_1 + beta_2 * REV1 + beta_3 * LOWVOL + ...
    This tells us which factors are driving the strategy's returns.
    """
    if verbose:
        print(f"\n  Decomposing {strategy_id} ({asset_class})...")

    # Get all signals
    all_signals = []
    for ticker, df in data.items():
        if len(df) < 260:
            continue
        try:
            kwargs = {}
            if strategy_id == "STR-I" and asset_class == "stock":
                kwargs["long_only"] = True
            sigs = scan_fn(df, ticker, **kwargs)
            if not sigs:
                continue
            for sig in sigs:
                sig["ticker"] = ticker
                sig["asset_class"] = asset_class
                all_signals.append(sig)
        except Exception:
            continue

    if not all_signals:
        return {"strategy_id": strategy_id, "error": "no signals", "n": 0}

    if verbose:
        print(f"    {len(all_signals)} signals found")

    # For each signal, compute factor exposures at entry date
    factor_exposures = []
    for sig in all_signals:
        ticker = sig["ticker"]
        entry_date = sig.get("date")
        r_mult = sig.get("r_multiple", 0)

        if ticker not in data or not entry_date:
            continue

        df = data[ticker]
        entry_date_ts = pd.Timestamp(entry_date) if not isinstance(entry_date, pd.Timestamp) else entry_date

        # Find the entry date in the data
        if entry_date_ts not in df.index:
            # Find closest date
            mask = df.index <= entry_date_ts
            if mask.sum() == 0:
                continue
            entry_date_ts = df.index[mask][-1]

        # Compute factor values at entry
        exposures = {"ticker": ticker, "r_multiple": r_mult, "direction": sig.get("direction", "long")}
        for factor_name in FACTOR_DEFS:
            sig_series = compute_factor_signal(df, factor_name)
            if entry_date_ts in sig_series.index:
                val = sig_series.loc[entry_date_ts]
                if not pd.isna(val):
                    exposures[factor_name] = float(val)
                else:
                    exposures[factor_name] = np.nan
            else:
                exposures[factor_name] = np.nan

        factor_exposures.append(exposures)

    if not factor_exposures:
        return {"strategy_id": strategy_id, "error": "no exposures", "n": 0}

    # Build DataFrame
    exposure_df = pd.DataFrame(factor_exposures)

    # Remove rows with NaN factor values
    factor_cols = list(FACTOR_DEFS.keys())
    clean_df = exposure_df.dropna(subset=factor_cols + ["r_multiple"])

    # Standardize factors to z-scores to prevent numerical issues
    # (LIQUID values can be in the billions, causing matrix inversion problems)
    for col in factor_cols:
        mean = clean_df[col].mean()
        std = clean_df[col].std()
        if std > 0:
            clean_df = clean_df.copy()
            clean_df[col] = (clean_df[col] - mean) / std

    if len(clean_df) < 10:
        return {"strategy_id": strategy_id, "error": "insufficient clean data", "n": len(clean_df)}

    if verbose:
        print(f"    {len(clean_df)} signals with complete factor data")

    # ── Factor correlation with R-multiple ──────────────────────────────────
    correlations = {}
    for factor in factor_cols:
        corr = clean_df["r_multiple"].corr(clean_df[factor])
        correlations[factor] = round(corr, 4)

    if verbose:
        print(f"\n    Factor correlations with R-multiple:")
        for f, c in sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True):
            print(f"      {f:15s}: {c:+.4f}")

    # ── Simple OLS regression: R = alpha + sum(beta_i * factor_i) ───────────
    # Using numpy for OLS (no scipy/sklearn dependency)
    Y = clean_df["r_multiple"].values.astype(float)
    X = clean_df[factor_cols].values.astype(float)
    X_with_const = np.column_stack([np.ones(len(X)), X])

    try:
        # OLS: beta = (X'X)^-1 X'Y
        betas = np.linalg.lstsq(X_with_const, Y, rcond=None)[0]
        betas = np.asarray(betas, dtype=float)
        residuals = Y - X_with_const @ betas
        n_obs, k = len(Y), len(factor_cols)
        ss_res = float(np.sum(residuals**2))
        ss_tot = float(np.sum((Y - np.mean(Y))**2))
        mse = ss_res / max(n_obs - k - 1, 1)

        # Standard errors
        xtx_inv = np.linalg.inv(X_with_const.T @ X_with_const)
        se = np.sqrt(np.diag(xtx_inv) * mse)
        t_stats = betas / se
        p_values = np.array([2 * (1 - NormalDist(0, 1).cdf(abs(float(t)))) for t in t_stats])

        # R-squared
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        regression = {
            "alpha": round(float(betas[0]), 4),
            "alpha_t": round(float(t_stats[0]), 3),
            "alpha_p": round(float(p_values[0]), 4),
            "r_squared": round(float(r_squared), 4),
            "n": n_obs,
            "coefficients": {},
        }
        for i, factor in enumerate(factor_cols):
            regression["coefficients"][factor] = {
                "beta": round(float(betas[i + 1]), 4),
                "t_stat": round(float(t_stats[i + 1]), 3),
                "p_value": round(float(p_values[i + 1]), 4),
            }

        if verbose:
            print(f"\n    Regression: R = alpha + sum(beta * factor)")
            print(f"    Alpha = {regression['alpha']:.4f} (t={regression['alpha_t']:.2f})")
            print(f"    R² = {regression['r_squared']:.4f}")
            for f, coef in regression["coefficients"].items():
                sig = "***" if coef["p_value"] < 0.01 else ("**" if coef["p_value"] < 0.05 else "")
                print(f"      {f:15s}: beta={coef['beta']:+.4f} (t={coef['t_stat']:.2f}, p={coef['p_value']:.4f}) {sig}")

    except Exception as e:
        regression = {"error": str(e)}

    # ── Factor quintile analysis: which quintile do signals come from? ─────
    quintile_dist = {}
    for factor in factor_cols:
        vals = clean_df[factor].values
        # Rank into quintiles within the signal set
        try:
            quintiles = pd.qcut(vals, 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"], duplicates="drop")
            dist = quintiles.value_counts().to_dict()
            avg_r_by_q = {}
            for q in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
                mask = quintiles == q
                if mask.sum() > 0:
                    avg_r_by_q[q] = round(float(clean_df.loc[mask, "r_multiple"].mean()), 4)
            quintile_dist[factor] = {"distribution": dist, "avg_r_by_quintile": avg_r_by_q}
        except Exception:
            quintile_dist[factor] = {"error": "could not compute"}

    return {
        "strategy_id": strategy_id,
        "asset_class": asset_class,
        "n_signals": len(all_signals),
        "n_clean": len(clean_df),
        "correlations": correlations,
        "regression": regression,
        "quintile_analysis": quintile_dist,
        "mean_r": round(float(clean_df["r_multiple"].mean()), 4),
    }


def run_full_analysis(verbose: bool = True) -> dict:
    """
    Run full factor analysis: factor premia + strategy decomposition.
    """
    print("=" * 70)
    print("HermesForge Factor Construction & Decomposition")
    print("=" * 70)

    print("\nLoading stock data...")
    stock_data = load_all_stocks()
    print(f"  {len(stock_data)} stock tickers loaded.")

    print("Loading crypto data...")
    crypto_data = load_all_crypto()
    print(f"  {len(crypto_data)} crypto symbols loaded.")

    # ── Part 1: Factor Premia ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("Part 1: Factor Premia Analysis")
    print(f"{'='*70}")
    print(f"\nLong-short quintile portfolios, monthly rebalance, after transaction costs.")
    print(f"Stocks: {COST_PER_TURN*100:.2f}% round-trip | Crypto: {COST_CRYPTO*100:.2f}% round-trip")

    all_results = {"factors": {}, "decomposition": {}}

    print(f"\n--- STOCKS ---")
    stock_factors = run_factor_analysis(stock_data, "stock", verbose=verbose)
    all_results["factors"]["stocks"] = stock_factors

    print(f"\n--- CRYPTO ---")
    crypto_factors = run_factor_analysis(crypto_data, "crypto", verbose=verbose)
    all_results["factors"]["crypto"] = crypto_factors

    # Factor summary table
    print(f"\n{'='*70}")
    print("Factor Premium Summary")
    print(f"{'='*70}")
    print(f"\n{'Factor':<15} {'Stock Ann.Ret':>14} {'Stock Sharpe':>13} {'Stock p':>8} "
          f"{'Crypto Ann.Ret':>15} {'Crypto Sharpe':>14} {'Crypto p':>9}")
    print("-" * 90)
    for factor in FACTOR_DEFS:
        s = stock_factors.get(factor, {})
        c = crypto_factors.get(factor, {})
        s_ret = f"{s.get('annualized_return', 0):+.2%}" if "error" not in s else "n/a"
        s_sharpe = f"{s.get('sharpe', 0):.2f}" if "error" not in s else "n/a"
        s_p = f"{s.get('p_value', 1):.4f}" if "error" not in s else "n/a"
        c_ret = f"{c.get('annualized_return', 0):+.2%}" if "error" not in c else "n/a"
        c_sharpe = f"{c.get('sharpe', 0):.2f}" if "error" not in c else "n/a"
        c_p = f"{c.get('p_value', 1):.4f}" if "error" not in c else "n/a"
        print(f"  {factor:<13} {s_ret:>14} {s_sharpe:>13} {s_p:>8} "
              f"{c_ret:>15} {c_sharpe:>14} {c_p:>9}")

    # ── Part 2: Strategy Decomposition ───────────────────────────────────────
    print(f"\n{'='*70}")
    print("Part 2: Strategy Return Decomposition")
    print(f"{'='*70}")

    # Decompose STR-B (stocks)
    print(f"\n--- STR-B MACD Divergence (Stocks) ---")
    str_b_decomp = decompose_strategy_returns(
        "STR-B", scan_b, stock_data, "stock", long_only=False, verbose=verbose
    )
    all_results["decomposition"]["STR-B_stocks"] = str_b_decomp

    # Decompose STR-I (stocks)
    print(f"\n--- STR-I AdaptiveTrend (Stocks) ---")
    str_i_decomp = decompose_strategy_returns(
        "STR-I", scan_i, stock_data, "stock", long_only=True, verbose=verbose
    )
    all_results["decomposition"]["STR-I_stocks"] = str_i_decomp

    # Decompose STR-B (crypto)
    print(f"\n--- STR-B MACD Divergence (Crypto) ---")
    str_b_crypto = decompose_strategy_returns(
        "STR-B", scan_b, crypto_data, "crypto", long_only=False, verbose=verbose
    )
    all_results["decomposition"]["STR-B_crypto"] = str_b_crypto

    # Decompose STR-I (crypto)
    print(f"\n--- STR-I AdaptiveTrend (Crypto) ---")
    str_i_crypto = decompose_strategy_returns(
        "STR-I", scan_i, crypto_data, "crypto", long_only=False, verbose=verbose
    )
    all_results["decomposition"]["STR-I_crypto"] = str_i_crypto

    # Decomposition summary
    print(f"\n{'='*70}")
    print("Decomposition Summary")
    print(f"{'='*70}")
    for key, result in all_results["decomposition"].items():
        if "error" in result:
            print(f"\n  {key}: {result['error']}")
            continue
        reg = result.get("regression", {})
        print(f"\n  {key}: {result['n_clean']} signals, mean R = {result['mean_r']}")
        if "r_squared" in reg:
            print(f"    R² = {reg['r_squared']:.4f}, Alpha = {reg['alpha']:.4f}")
            for f, coef in reg.get("coefficients", {}).items():
                sig = "***" if coef["p_value"] < 0.01 else ("**" if coef["p_value"] < 0.05 else "")
                print(f"    {f}: beta={coef['beta']:+.4f} (p={coef['p_value']:.4f}) {sig}")

    return all_results


def main():
    ap = argparse.ArgumentParser(
        description="HermesForge factor construction & decomposition"
    )
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--factor", type=str, default=None, help="Single factor detail")
    args = ap.parse_args()

    results = run_full_analysis(verbose=True)

    if args.json:
        def clean(d):
            if isinstance(d, dict):
                return {k: clean(v) for k, v in d.items()}
            if isinstance(d, list):
                return [clean(x) for x in d]
            if isinstance(d, (np.integer, np.floating)):
                return float(d)
            if isinstance(d, np.bool_):
                return bool(d)
            if isinstance(d, pd.Timestamp):
                return str(d)
            return d
        print("\n--- JSON OUTPUT ---")
        print(json.dumps(clean(results), indent=2, default=str))


if __name__ == "__main__":
    main()