"""
Correlation State Module (PROP-001)
Computes BTC beta, rolling correlations, beta clustering,
and portfolio concentration risk.
"""

import math
import statistics


# ── Constants ──────────────────────────────────────────────────────────────
DEFAULT_WINDOW = 72

# Cluster thresholds (simple percentile / threshold split)
LOW_BETA_THRESHOLD = 0.7
HIGH_BETA_THRESHOLD = 1.3
# CLUSTER_LOW = 0, CLUSTER_MEDIUM = 1, CLUSTER_HIGH = 2

# Portfolio concentration default threshold: flag if any cluster > 50%
CONCENTRATION_THRESHOLD = 0.50


# ── BTC Beta ──────────────────────────────────────────────────────────────

def compute_btc_beta(symbol_returns: list, btc_returns: list,
                     window: int = DEFAULT_WINDOW) -> float:
    """
    Compute rolling OLS beta of symbol returns against BTC returns
    over the last `window` periods.

    beta = Cov(symbol, btc) / Var(btc)

    Args:
        symbol_returns: list of floats (percentage returns as decimals)
        btc_returns: list of floats (percentage returns as decimals)
        window: lookback window (default 72)

    Returns:
        float: beta coefficient. Returns 0.0 if insufficient data or
               zero BTC variance.
    """
    if len(symbol_returns) < 2 or len(btc_returns) < 2:
        return 0.0

    # Use at most `window` most recent observations
    sym = symbol_returns[-window:]
    btc = btc_returns[-window:]

    # Trim to same length
    n = min(len(sym), len(btc))
    sym = sym[-n:]
    btc = btc[-n:]

    if n < 2:
        return 0.0

    mean_sym = statistics.mean(sym)
    mean_btc = statistics.mean(btc)

    # Covariance: sum((x_i - x̄)(y_i - ȳ)) / (n - 1)
    cov = sum((s - mean_sym) * (b - mean_btc) for s, b in zip(sym, btc)) / (n - 1)

    # Variance of BTC returns
    var_btc = sum((b - mean_btc) ** 2 for b in btc) / (n - 1)

    if var_btc == 0:
        return 0.0

    return cov / var_btc


# ── Correlation ───────────────────────────────────────────────────────────

def compute_correlation(symbol_returns: list, btc_returns: list,
                        window: int = DEFAULT_WINDOW) -> float:
    """
    Compute rolling Pearson correlation between symbol and BTC returns.

    Args:
        symbol_returns: list of floats
        btc_returns: list of floats
        window: lookback window (default 72)

    Returns:
        float: Pearson r in [-1, 1]. Returns 0.0 if insufficient data
               or zero variance.
    """
    if len(symbol_returns) < 2 or len(btc_returns) < 2:
        return 0.0

    sym = symbol_returns[-window:]
    btc = btc_returns[-window:]

    n = min(len(sym), len(btc))
    sym = sym[-n:]
    btc = btc[-n:]

    if n < 2:
        return 0.0

    # Use statistics.correlation (Python 3.10+)
    try:
        return statistics.correlation(sym, btc)
    except statistics.StatisticsError:
        return 0.0


# ── Beta Clustering ───────────────────────────────────────────────────────

def cluster_by_beta(betas: dict) -> dict:
    """
    Group symbols into beta clusters using threshold-based split.

    Clusters:
      - 0: low beta  (< 0.7)
      - 1: medium beta (0.7 - 1.3)
      - 2: high beta (> 1.3)

    Args:
        betas: dict of {symbol: beta_value}

    Returns:
        dict of {symbol: cluster_id}
    """
    clusters = {}
    for symbol, beta in betas.items():
        if beta < LOW_BETA_THRESHOLD:
            clusters[symbol] = 0
        elif beta <= HIGH_BETA_THRESHOLD:
            clusters[symbol] = 1
        else:
            clusters[symbol] = 2
    return clusters


# ── Portfolio Concentration ───────────────────────────────────────────────

def portfolio_concentration(positions: dict, cluster_map: dict,
                            threshold: float = CONCENTRATION_THRESHOLD) -> dict:
    """
    Compute exposure per cluster and flag overconcentration.

    Args:
        positions: dict of {symbol: exposure_usd}
        cluster_map: dict of {symbol: cluster_id}
        threshold: fraction of total exposure that triggers a flag (default 0.50)

    Returns:
        dict:
            'cluster_exposures': {cluster_id: total_usd}
            'total_exposure': float
            'cluster_pcts': {cluster_id: fraction_of_total}
            'flags': list of cluster_ids that exceed threshold
            'overconcentrated': bool (True if any cluster flagged)
    """
    if not positions:
        return {
            'cluster_exposures': {},
            'total_exposure': 0.0,
            'cluster_pcts': {},
            'flags': [],
            'overconcentrated': False,
        }

    cluster_exposures = {}
    total_exposure = 0.0

    for symbol, exposure in positions.items():
        total_exposure += abs(exposure)
        cluster_id = cluster_map.get(symbol, -1)
        cluster_exposures[cluster_id] = cluster_exposures.get(cluster_id, 0.0) + abs(exposure)

    if total_exposure == 0:
        return {
            'cluster_exposures': cluster_exposures,
            'total_exposure': 0.0,
            'cluster_pcts': {},
            'flags': [],
            'overconcentrated': False,
        }

    cluster_pcts = {}
    flags = []
    for cid, exp in cluster_exposures.items():
        pct = exp / total_exposure
        cluster_pcts[cid] = pct
        if pct > threshold:
            flags.append(cid)

    return {
        'cluster_exposures': cluster_exposures,
        'total_exposure': total_exposure,
        'cluster_pcts': cluster_pcts,
        'flags': flags,
        'overconcentrated': len(flags) > 0,
    }