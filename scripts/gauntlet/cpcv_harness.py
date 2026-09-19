"""
cpcv_harness.py — Combinatorial Purged Cross-Validation per López de Prado (2018).

Implements CPCV for backtest overfitting assessment:
- Chronological group splitting (no lookahead)
- Purge + embargo for financial serial dependence
- Path reconstruction for full-sample coverage
- PBO (Probability of Backtest Overfitting)
- DSR (Deflated Sharpe Ratio)
"""

from __future__ import annotations

import itertools
import math
from collections import defaultdict
from typing import Any


# ── 1. Group splitting ──────────────────────────────────────────────────────

def split_trades_into_groups(
    trades: list[dict[str, Any]],
    n_groups: int = 12,
) -> list[list[dict[str, Any]]]:
    """
    Split trades into n_groups by chronological order (entry_time).

    Each group receives approximately len(trades) // n_groups trades.
    The remainder is distributed one per group from the earliest groups.
    Returns list of groups, each group is a list of trade dicts.
    """
    if not trades:
        return [[] for _ in range(n_groups)]

    # Sort chronologically by entry_time
    sorted_trades = sorted(trades, key=lambda t: t["entry_time"])
    total = len(sorted_trades)
    base_size = total // n_groups
    remainder = total % n_groups

    groups: list[list[dict[str, Any]]] = []
    idx = 0
    for g in range(n_groups):
        size = base_size + (1 if g < remainder else 0)
        groups.append(sorted_trades[idx : idx + size])
        idx += size

    return groups


# ── 2. Purge + Embargo ──────────────────────────────────────────────────────

def purge_and_embargo(
    train_groups: list[list[dict[str, Any]]],
    test_groups: list[list[dict[str, Any]]],
    holding_horizon_bars: int = 20,
    embargo_bars: int = 40,
) -> list[dict[str, Any]]:
    """
    Remove training trades that overlap or leak information about the test set.

    Purge: remove train trades whose exit is within holding_horizon_bars BEFORE
           the test window, or that overlap the test window entirely.
    Embargo: remove train trades whose entry falls within embargo_bars AFTER
             the test window end.

    Returns cleaned list of training trades.
    """
    if not test_groups:
        return [t for g in train_groups for t in g]

    all_test = [t for g in test_groups for t in g]
    test_start = min(t["entry_time"] for t in all_test)
    test_end = max(t["exit_time"] for t in all_test)

    # Purge boundary: trades closing after this point may still be active
    purge_boundary = test_start - holding_horizon_bars
    # Embargo boundary: trades opening before this point may leak info
    embargo_boundary = test_end + embargo_bars

    all_train = [t for g in train_groups for t in g]
    clean: list[dict[str, Any]] = []

    for trade in all_train:
        # Purge: trade overlaps with test window (or closing too close to it)
        if trade["exit_time"] >= purge_boundary and trade["entry_time"] <= test_end:
            continue
        # Embargo: trade opens too soon after test window
        if trade["entry_time"] <= embargo_boundary and trade["entry_time"] > test_end:
            continue
        clean.append(trade)

    return clean


# ── 3. CPCV split generation ────────────────────────────────────────────────

def generate_cpcv_splits(
    trades: list[dict[str, Any]],
    n_groups: int = 12,
    k_test: int = 2,
    holding_horizon_bars: int = 20,
    embargo_bars: int = 40,
) -> list[dict[str, Any]]:
    """
    Generate all C(n_groups, k_test) CPCV splits.

    Each split dict:
        {
            "train_indices": [...],   # indices into original trades list
            "test_indices": [...],
            "train_trades": [...],    # actual trade dicts (after purge+embargo)
            "test_trades": [...],
            "test_groups": [...]      # which group indices are test
        }
    """
    if not trades:
        return []

    groups = split_trades_into_groups(trades, n_groups)
    group_indices = list(range(n_groups))

    # Map each trade to its global index for traceability
    trade_to_index: dict[int, int] = {}
    idx = 0
    for group in groups:
        for trade in group:
            trade_to_index[id(trade)] = idx
            idx += 1

    splits: list[dict[str, Any]] = []

    for test_group_combo in itertools.combinations(group_indices, k_test):
        test_set = set(test_group_combo)
        train_set = set(group_indices) - test_set

        test_groups_list = [groups[g] for g in test_group_combo]
        train_groups_list = [groups[g] for g in train_set]

        test_trades = [t for g in test_groups_list for t in g]
        train_trades = purge_and_embargo(
            train_groups_list, test_groups_list,
            holding_horizon_bars, embargo_bars,
        )

        test_indices = [trade_to_index[id(t)] for t in test_trades]
        train_indices = [trade_to_index[id(t)] for t in train_trades]

        splits.append({
            "train_indices": train_indices,
            "test_indices": test_indices,
            "train_trades": train_trades,
            "test_trades": test_trades,
            "test_groups": list(test_group_combo),
        })

    return splits


# ── 4. Path reconstruction ──────────────────────────────────────────────────

def reconstruct_paths(
    splits: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    """
    Reconstruct paths from CPCV splits via 1-factorization of the complete graph.

    Each path is a sequence of splits whose test groups are pairwise disjoint
    and collectively cover all groups exactly once (a perfect matching of K_N).

    With n_groups=12, k_test=2: exactly 11 paths of 6 splits each.
    Uses the circle method (round-robin tournament schedule) to decompose
    K_N into N-1 perfect matchings.
    """
    if not splits:
        return []

    # Determine n_groups from splits
    all_test_groups: set[int] = set()
    for s in splits:
        all_test_groups.update(s["test_groups"])
    n_groups = len(all_test_groups)

    if n_groups < 2:
        return []

    # Build lookup: (min_g, max_g) → split
    split_lookup: dict[tuple[int, int], dict[str, Any]] = {}
    for s in splits:
        tg = tuple(sorted(s["test_groups"]))
        split_lookup[tg] = s  # last wins if duplicate (shouldn't happen)

    # 1-factorization of K_N (N even) using the circle method.
    # Fix vertex N-1 at center; arrange 0..N-2 in a circle.
    # N-1 here because k_test=2 assumes pairs; generalize if needed.
    if n_groups % 2 != 0:
        # Odd N: add a dummy, then remove dummy edges at the end
        # But for CPCV with k_test=2, n_groups is typically even
        n = n_groups + 1
        has_dummy = True
    else:
        n = n_groups
        has_dummy = False

    center = n - 1  # vertex n-1 is the fixed center
    circle_size = n - 1  # vertices 0..n-2 on the circle

    paths: list[list[dict[str, Any]]] = []

    for round_idx in range(circle_size):
        path_splits: list[dict[str, Any]] = []
        # Center pairing
        a, b = center, round_idx
        if not has_dummy or (a < n_groups and b < n_groups):
            key = (min(a, b), max(a, b))
            if key in split_lookup:
                path_splits.append(split_lookup[key])

        # Circle pairings
        for k in range(1, circle_size // 2 + 1):
            a = (round_idx - k) % circle_size
            b = (round_idx + k) % circle_size
            if a == b:
                continue
            if not has_dummy or (a < n_groups and b < n_groups):
                key = (min(a, b), max(a, b))
                if key in split_lookup:
                    path_splits.append(split_lookup[key])

        if path_splits:
            paths.append(path_splits)

    return paths


# ── 5. Split metrics ────────────────────────────────────────────────────────

def compute_split_metrics(
    split: dict[str, Any],
) -> dict[str, float]:
    """
    Compute performance metrics for a single CPCV split.

    Returns: {sharpe, avg_r, pf, win_rate, trade_count}
    Uses test trades to compute metrics.
    """
    trades = split.get("test_trades", [])
    if not trades:
        return {
            "sharpe": 0.0,
            "avg_r": 0.0,
            "pf": 0.0,
            "win_rate": 0.0,
            "trade_count": 0,
        }

    pnls = [t["pnl_bps"] for t in trades]
    n = len(pnls)
    avg = sum(pnls) / n

    # Sharpe: mean / std (annualized equivalent, but here per-trade)
    if n > 1:
        variance = sum((p - avg) ** 2 for p in pnls) / (n - 1)
        std = math.sqrt(variance) if variance > 1e-15 else 1e-15
        sharpe = avg / std
    else:
        sharpe = 0.0

    # Profit factor: gross profit / gross loss
    gross_profit = sum(p for p in pnls if p > 0)
    gross_loss = abs(sum(p for p in pnls if p < 0))
    pf = gross_profit / gross_loss if gross_loss > 1e-15 else (gross_profit if gross_profit > 0 else 0.0)

    # Win rate
    wins = sum(1 for p in pnls if p > 0)
    win_rate = wins / n if n > 0 else 0.0

    return {
        "sharpe": round(sharpe, 6),
        "avg_r": round(avg, 6),
        "pf": round(pf, 6),
        "win_rate": round(win_rate, 6),
        "trade_count": n,
    }


# ── 6. PBO (Probability of Backtest Overfitting) ────────────────────────────

def compute_pbo(
    split_metrics: list[dict[str, float]],
) -> float:
    """
    Compute Probability of Backtest Overfitting.

    For each split, compare IS performance rank against OOS performance rank.
    When only one set of metrics per split is provided (single strategy),
    PBO is approximated from the distribution of Sharpe ratios across splits:
    the fraction of splits where the IS Sharpe ranks worse than the OOS Sharpe.

    Uses dense ranking (ties get the same rank) so that identical Sharpes
    produce PBO = 0.

    Returns PBO ∈ [0, 1], where lower is better.
    """
    if len(split_metrics) < 2:
        return 0.0

    sharpes = [m.get("sharpe", 0.0) for m in split_metrics]
    n = len(sharpes)

    # Dense ranking: ties get the same rank (0 = best)
    # Sort unique Sharpe values descending, then assign ranks
    unique_desc = sorted(set(sharpes), reverse=True)
    sharpe_to_rank = {s: rank for rank, s in enumerate(unique_desc)}
    ranks = [sharpe_to_rank[s] for s in sharpes]

    # For each split: IS rank vs OOS rank (next split wraps around)
    overfit_count = 0
    for i in range(n):
        is_rank = ranks[i]
        oos_rank = ranks[(i + 1) % n]
        if is_rank > oos_rank:
            overfit_count += 1

    return overfit_count / n


# ── 7. DSR (Deflated Sharpe Ratio) ──────────────────────────────────────────

def _norm_cdf(x: float) -> float:
    """Standard normal CDF using the error function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Standard normal PPF (quantile) using rational approximation."""
    if p <= 0.0:
        return -float("inf")
    if p >= 1.0:
        return float("inf")

    # Rational approximation for the inverse error function
    a = 0.147
    y = 2.0 * p - 1.0
    part1 = math.log(1.0 - y * y)
    part2 = 2.0 / (math.pi * a) + part1 / 2.0
    sign = 1.0 if y >= 0 else -1.0
    result = sign * math.sqrt(math.sqrt(part2 * part2 - part1 / a) - part2)
    return result * math.sqrt(2.0)


def compute_dsr(
    sharpe: float,
    skew: float,
    kurtosis: float,
    n_trials: int,
    n_observations: int,
) -> float:
    """
    Compute Deflated Sharpe Ratio (Bailey & López de Prado, 2014).

    DSR = Φ( (sharpe * √n_obs - E[max]) / √V[max] )

    where E[max] and V[max] are the expected value and variance of the
    maximum Sharpe ratio from n_trials under the null hypothesis of zero
    expected Sharpe.

    Returns the probability that the observed Sharpe ratio exceeds the
    selection-adjusted benchmark.
    """
    if n_trials < 1 or n_observations < 1:
        return 0.0

    # Expected maximum of n_trials i.i.d. standard normal draws
    # Using asymptotic approximation from extreme value theory:
    # E[max] ≈ (1 - γ) * Z + γ * Z₁  where γ ≈ 0.5772 (Euler-Mascheroni)
    gamma = 0.5772156649015329  # Euler-Mascheroni constant

    # Z = Φ^{-1}(1 - 1/n_trials)
    alpha = 1.0 - 1.0 / n_trials
    Z = _norm_ppf(alpha)

    # Z₁ is a slightly more extreme quantile
    alpha1 = 1.0 - 1.0 / (n_trials * math.e)
    Z1 = _norm_ppf(alpha1)

    # Expected maximum (E[max])
    e_max = (1.0 - gamma) * Z + gamma * Z1

    # Variance of the maximum
    # V[max] ≈ (π²/6) / log(n_trials) ... more precisely:
    # V[max] ≈ 1 / (N * φ(Z)²) — variance of the maximum order statistic
    # φ(Z) is the standard normal PDF evaluated at Z
    _phi_z = math.exp(-0.5 * Z * Z) / math.sqrt(2.0 * math.pi)
    v_max = 1.0 / (n_trials * _phi_z * _phi_z) if abs(Z) > 1e-15 and _phi_z > 1e-15 else 1e-15

    if v_max <= 0.0:
        v_max = 1e-15

    # Adjust for skew and kurtosis (simplified — Bailey & López de Prado note
    # that non-normal returns affect the null distribution)
    # Here we use the raw approximation; skew/kurtosis are accepted as inputs
    # for future refinement but the core DSR uses normal approximation.

    # DSR numerator
    t_stat = sharpe * math.sqrt(n_observations)
    dsr_num = t_stat - e_max
    dsr_den = math.sqrt(v_max)

    dsr_z = dsr_num / dsr_den
    dsr = _norm_cdf(dsr_z)

    return round(max(0.0, min(1.0, dsr)), 6)


# ── 8. Full CPCV pipeline ───────────────────────────────────────────────────

def run_cpcv(
    trades: list[dict[str, Any]],
    n_groups: int = 12,
    k_test: int = 2,
    n_trials_from_ledger: int | None = None,
    holding_horizon_bars: int = 20,
    embargo_bars: int = 40,
) -> dict[str, Any]:
    """
    Run the full CPCV pipeline.

    Args:
        trades: list of trade dicts with {entry_time, exit_time, pnl_bps, ...}
        n_groups: number of chronological groups
        k_test: number of test groups per split
        n_trials_from_ledger: N for DSR (if None, uses len(trades) as proxy)
        holding_horizon_bars: purge window before test
        embargo_bars: embargo window after test

    Returns:
        {
            "splits": [...],
            "paths": [...],
            "split_metrics": [...],
            "pbo": float,
            "dsr": float,
            "n_splits": int,
            "n_paths": int,
        }
    """
    # Generate splits
    splits = generate_cpcv_splits(
        trades, n_groups, k_test, holding_horizon_bars, embargo_bars,
    )

    # Reconstruct paths
    paths = reconstruct_paths(splits)

    # Compute per-split metrics
    split_metrics = [compute_split_metrics(s) for s in splits]

    # Compute PBO
    pbo = compute_pbo(split_metrics)

    # Compute DSR
    n_trials = n_trials_from_ledger if n_trials_from_ledger is not None else len(trades)
    n_trials = max(1, n_trials)

    # Aggregate Sharpe from all split test trades
    all_test_trades = []
    for s in splits:
        all_test_trades.extend(s["test_trades"])

    if all_test_trades:
        pnls = [t["pnl_bps"] for t in all_test_trades]
        n_obs = len(pnls)
        avg = sum(pnls) / n_obs
        if n_obs > 1:
            var = sum((p - avg) ** 2 for p in pnls) / (n_obs - 1)
            std = math.sqrt(var) if var > 1e-15 else 1e-15
            sharpe = avg / std
        else:
            sharpe = 0.0
            std = 0.0

        # Skewness
        if n_obs > 2 and std > 1e-15:
            skew = sum(((p - avg) / std) ** 3 for p in pnls) * n_obs / ((n_obs - 1) * (n_obs - 2))
        else:
            skew = 0.0

        # Kurtosis
        if n_obs > 3 and std > 1e-15:
            kurt = (
                sum(((p - avg) / std) ** 4 for p in pnls)
                * n_obs * (n_obs + 1)
                / ((n_obs - 1) * (n_obs - 2) * (n_obs - 3))
                - 3.0 * (n_obs - 1) ** 2 / ((n_obs - 2) * (n_obs - 3))
            )
        else:
            kurt = 0.0

        dsr = compute_dsr(sharpe, skew, kurt, n_trials, n_obs)
    else:
        sharpe = 0.0
        dsr = 1.0  # no data → cannot reject

    return {
        "splits": splits,
        "paths": paths,
        "split_metrics": split_metrics,
        "pbo": round(pbo, 6),
        "dsr": round(dsr, 6),
        "sharpe": round(sharpe, 6) if all_test_trades else 0.0,
        "n_splits": len(splits),
        "n_paths": len(paths),
    }