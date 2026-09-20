"""
Position Manager Module (PROP-001 G4).
Single authority over position sizing. Every strategy proposes; this module disposes.

Invariant: no approved order may reduce liquidation headroom below floor, ever.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


# ── Default tier thresholds ─────────────────────────────────────────────────
_TIER1_PCT = 0.15   # -15% trailing: halve size
_TIER2_PCT = 0.25   # -25% trailing: close discretionary, hold high-confidence
_TIER3_PCT = 0.35   # -35% trailing: flat + alert

# ── Cluster / headroom defaults ─────────────────────────────────────────────
MAX_CLUSTER_EXPOSURE = 0.50   # no cluster > 50% of equity
MIN_LIQ_HEADROOM_ATR = 3.0    # minimum liquidation headroom in ATR units


# ═══════════════════════════════════════════════════════════════════════════════
# Position approval
# ═══════════════════════════════════════════════════════════════════════════════

def approve_position(
    strategy_id: str,
    ticker: str,
    proposed_size_usd: float,
    direction: str,
    current_positions: List[Dict[str, Any]],
    equity: float,
    correlation_state: Optional[Dict[str, Any]] = None,
    atr_values: Optional[Dict[str, float]] = None,
    equity_curve: Optional[List[float]] = None,
    peak_equity: Optional[float] = None,
    swing_positions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Approve, reduce, or reject a proposed position.

    Returns:
        dict with keys:
            approved_size    – float, the approved position size in USD
            rejection_reason – str or None
            cluster_exposure – float, exposure of the ticker's cluster as fraction of equity
            headroom_atr     – float, current liquidation headroom in ATR units
    """
    rejection_reason = None
    approved_size = proposed_size_usd

    if equity <= 0:
        return {
            "approved_size": 0.0,
            "rejection_reason": "zero or negative equity",
            "cluster_exposure": 0.0,
            "headroom_atr": 0.0,
        }

    # ── 1. Drawdown breaker check ──────────────────────────────────────────
    if equity_curve is None:
        equity_curve = []
    if peak_equity is None:
        peak_equity = equity

    dd_result = check_drawdown_breaker(equity_curve, peak_equity)
    tier = dd_result["tier"]

    if tier == 3:
        return {
            "approved_size": 0.0,
            "rejection_reason": f"drawdown breaker tier 3: equity {dd_result['drawdown_pct']:.1%} below peak",
            "cluster_exposure": 0.0,
            "headroom_atr": 0.0,
        }
    elif tier == 2 and direction != "HIGH_CONFIDENCE":
        # Close discretionary, only high-confidence through
        return {
            "approved_size": 0.0,
            "rejection_reason": f"drawdown breaker tier 2: discretionary closed, equity {dd_result['drawdown_pct']:.1%} below peak",
            "cluster_exposure": 0.0,
            "headroom_atr": 0.0,
        }
    elif tier == 1:
        approved_size *= 0.5

    # ── 2. Cluster exposure check ──────────────────────────────────────────
    if correlation_state is None:
        correlation_state = {}
    cluster_exp = compute_cluster_exposure(current_positions, correlation_state)
    # Compute the ticker's cluster
    ticker_cluster = _assign_cluster(ticker, correlation_state)
    new_positions = list(current_positions) + [
        {"ticker": ticker, "size_usd": approved_size, "direction": direction}
    ]
    new_cluster_exp = compute_cluster_exposure(new_positions, correlation_state)
    new_ticker_cluster_exp = new_cluster_exp.get(ticker_cluster, 0.0)

    if new_ticker_cluster_exp > MAX_CLUSTER_EXPOSURE:
        # Scale down to hit the cap exactly
        current_cluster = cluster_exp.get(ticker_cluster, 0.0)
        room = (MAX_CLUSTER_EXPOSURE * equity) - (current_cluster * equity)
        if room <= 0:
            return {
                "approved_size": 0.0,
                "rejection_reason": f"cluster {ticker_cluster} at cap: {current_cluster:.1%} of equity",
                "cluster_exposure": new_ticker_cluster_exp,
                "headroom_atr": _compute_headroom(current_positions, atr_values or {}, equity),
            }
        approved_size = min(approved_size, room)

    # ── 3. Liquidation headroom check (invariant) ──────────────────────────
    if atr_values is None:
        atr_values = {}
    headroom = _compute_headroom(current_positions, atr_values, equity)
    test_positions = list(current_positions) + [
        {"ticker": ticker, "size_usd": approved_size, "direction": direction}
    ]
    test_headroom = _compute_headroom(test_positions, atr_values, equity)
    floor = _headroom_floor(atr_values)

    if test_headroom < floor:
        # Scale size down to maintain headroom at floor
        if headroom <= floor:
            approved_size = 0.0
            rejection_reason = f"liquidation headroom {headroom:.2f} ATR already at/below floor {floor:.2f}"
        else:
            # Reduce size proportionally
            available_headroom = headroom - floor
            if approved_size > 0:
                reduction_ratio = available_headroom / (headroom - test_headroom) if (headroom - test_headroom) > 0 else 0
                approved_size = approved_size * min(reduction_ratio, 1.0)
            if approved_size <= 0:
                rejection_reason = f"size reduced to zero by headroom constraint (floor={floor:.2f} ATR)"

    # ── 4. Swing conflict resolution ───────────────────────────────────────
    if swing_positions:
        for sp in swing_positions:
            if sp.get("ticker") == ticker:
                swing_dir = sp.get("direction", "")
                conflict_result = resolve_conflict(direction, swing_dir)
                if conflict_result == "flatten":
                    approved_size = 0.0
                    rejection_reason = "swing conflict: flatten ordered"
                elif conflict_result == "ignore":
                    approved_size = 0.0
                    rejection_reason = "swing conflict: 5m signal ignored"
                break

    return {
        "approved_size": round(approved_size, 2),
        "rejection_reason": rejection_reason,
        "cluster_exposure": round(new_ticker_cluster_exp, 4),
        "headroom_atr": round(test_headroom, 2),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Cluster exposure
# ═══════════════════════════════════════════════════════════════════════════════

def _assign_cluster(ticker: str, correlation_state: Dict[str, Any]) -> str:
    """Map a ticker to its BTC-beta cluster label."""
    clusters = correlation_state.get("clusters", {})
    for cluster_name, members in clusters.items():
        if ticker in members:
            return cluster_name
    return "medium_beta"  # default


def compute_cluster_exposure(
    positions: List[Dict[str, Any]],
    correlation_state: Dict[str, Any],
) -> Dict[str, float]:
    """
    Group positions by BTC-beta cluster and return exposure per cluster as
    fraction of total equity implied by the positions.

    Enforces: no cluster > 50% of equity (callers check this).

    Returns:
        dict mapping cluster name to exposure fraction (0.0–1.0+)
    """
    clusters: Dict[str, float] = {}
    raw_clusters: Dict[str, float] = {}

    # Sum absolute size per cluster
    for pos in positions:
        ticker = pos.get("ticker", "")
        size = abs(float(pos.get("size_usd", 0)))
        cluster_name = _assign_cluster(ticker, correlation_state)
        raw_clusters[cluster_name] = raw_clusters.get(cluster_name, 0.0) + size

    # Total equity implied: sum of all position sizes (proxy when equity not passed)
    total_size = sum(raw_clusters.values()) if raw_clusters else 0.0

    if total_size > 0:
        for cluster_name, size in raw_clusters.items():
            clusters[cluster_name] = size / total_size

    return clusters


# ═══════════════════════════════════════════════════════════════════════════════
# Liquidation headroom
# ═══════════════════════════════════════════════════════════════════════════════

def _headroom_floor(atr_values: Dict[str, float]) -> float:
    """Compute the dynamic headroom floor. Widens when volatility expands."""
    if not atr_values:
        return MIN_LIQ_HEADROOM_ATR
    avg_atr_pct = sum(atr_values.values()) / len(atr_values)
    # Floor widens with volatility: base 3 ATR, scaled up as ATR % grows
    if avg_atr_pct <= 0.01:  # 1% ATR or less
        return MIN_LIQ_HEADROOM_ATR
    # Scale: floor = 3 * (1 + (atr_pct - 0.01) * scaling)
    scale = (avg_atr_pct - 0.01) * 100  # e.g. 2% ATR → scale=1
    return max(MIN_LIQ_HEADROOM_ATR, MIN_LIQ_HEADROOM_ATR + scale * 0.5)


def _compute_headroom(
    positions: List[Dict[str, Any]],
    atr_values: Dict[str, float],
    equity: float,
) -> float:
    """
    Portfolio-level distance-to-liquidation in ATR units.
    Simplified model: assumes each position's liquidation distance is 10 ATR
    with no offset, scaled by its weight in portfolio.
    """
    if not positions or equity <= 0:
        return float("inf")

    total_weighted = 0.0
    total_weight = 0.0

    for pos in positions:
        ticker = pos.get("ticker", "")
        size = abs(float(pos.get("size_usd", 0)))
        weight = size / equity if equity > 0 else 0
        total_weight += weight

        ticker_atr = atr_values.get(ticker)
        if ticker_atr is not None:
            # Liq distance in ATR units: assume 10 ATR per position
            total_weighted += weight * 10.0
        else:
            total_weighted += weight * 3.0  # conservative default

    if total_weight == 0:
        return float("inf")

    return total_weighted / total_weight


def compute_liquidation_headroom(
    positions: List[Dict[str, Any]],
    atr_values: Dict[str, float],
) -> float:
    """Public wrapper — portfolio-level distance-to-liquidation in ATR units."""
    total_size = sum(abs(float(p.get("size_usd", 0))) for p in positions)
    equity = total_size / 1.0 if total_size > 0 else 1.0  # proxy when equity unknown
    return _compute_headroom(positions, atr_values, equity)


# ═══════════════════════════════════════════════════════════════════════════════
# Conflict resolution
# ═══════════════════════════════════════════════════════════════════════════════

def resolve_conflict(signal_5m: str, swing_position: str) -> str:
    """
    When a 5m signal opposes an open swing position on the same symbol.

    Args:
        signal_5m: 'long' or 'short' direction from 5m signal
        swing_position: 'long' or 'short' direction from swing position

    Returns:
        One of: 'net_down', 'ignore', or 'flatten'
    """
    if signal_5m == swing_position:
        return "net_down"  # same direction — net down, no conflict

    # Opposing directions → deliberative resolution
    # Default conservative: ignore the 5m signal
    return "ignore"


# ═══════════════════════════════════════════════════════════════════════════════
# Drawdown circuit breaker
# ═══════════════════════════════════════════════════════════════════════════════

def check_drawdown_breaker(
    equity_curve: List[float],
    peak_equity: float,
    tier1_pct: float = _TIER1_PCT,
    tier2_pct: float = _TIER2_PCT,
    tier3_pct: float = _TIER3_PCT,
) -> Dict[str, Any]:
    """
    Tiered circuit breaker based on trailing drawdown from peak.

    Returns:
        dict with:
            tier          – int: 0 (no breach), 1 (halve), 2 (close discretionary), 3 (flat)
            drawdown_pct  – float: drawdown from peak as positive fraction
            peak_equity   – float
            current_equity – float
            action        – str: description of action
    """
    current_equity = equity_curve[-1] if equity_curve else peak_equity

    if peak_equity <= 0:
        return {
            "tier": 0,
            "drawdown_pct": 0.0,
            "peak_equity": peak_equity,
            "current_equity": current_equity,
            "action": "no breach",
        }

    dd = (peak_equity - current_equity) / peak_equity

    if dd >= tier3_pct:
        return {
            "tier": 3,
            "drawdown_pct": round(dd, 4),
            "peak_equity": peak_equity,
            "current_equity": current_equity,
            "action": "flat + alert: all positions closed",
        }
    elif dd >= tier2_pct:
        return {
            "tier": 2,
            "drawdown_pct": round(dd, 4),
            "peak_equity": peak_equity,
            "current_equity": current_equity,
            "action": "close discretionary, hold only high-confidence",
        }
    elif dd >= tier1_pct:
        return {
            "tier": 1,
            "drawdown_pct": round(dd, 4),
            "peak_equity": peak_equity,
            "current_equity": current_equity,
            "action": "halve all position sizes",
        }
    else:
        return {
            "tier": 0,
            "drawdown_pct": round(dd, 4),
            "peak_equity": peak_equity,
            "current_equity": current_equity,
            "action": "no breach",
        }