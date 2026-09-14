"""
Crypto Regime Module (PROP-001).

Parallel implementation with interface-compatible `tag_signal()` so strategy
selectors work unchanged. Uses crypto-native components: BTC multi-timeframe
trend, cross-sectional funding dispersion, aggregate OI trend, stablecoin net
flow, and BTC realised-vol percentile.

Interface matches regime_filter.py:
    get_regime(as_of=None, asset_class='crypto') -> dict
    tag_signal(signal: dict, regime: dict | None) -> dict
"""

from __future__ import annotations

import statistics
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sma(values: np.ndarray, window: int) -> np.ndarray:
    """Simple moving average. Returns NaN-padded array of same length."""
    if len(values) < window:
        return np.full_like(values, np.nan)
    out = np.full_like(values, np.nan)
    out[window - 1:] = np.convolve(values, np.ones(window) / window, mode='valid')
    return out


def _ensure_numeric(arr) -> np.ndarray:
    """Convert input to clean float ndarray, dropping NaN."""
    a = np.asarray(arr, dtype=float)
    return a[np.isfinite(a)]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_absent(x) -> bool:
    """Return True if x is None or an empty array/dict."""
    if x is None:
        return True
    try:
        return len(x) == 0
    except TypeError:
        return False


# ---------------------------------------------------------------------------
# Component: BTC multi-timeframe trend
# ---------------------------------------------------------------------------

def _compute_btc_trend(btc_data: np.ndarray) -> Dict[str, Any]:
    """
    Multi-timeframe BTC trend assessment.

    Args:
        btc_data: 1-D array of BTC closing prices (newest last).

    Returns:
        dict with {trend, score, regime, sma_50, sma_200, sma_20, alignment}.
    """
    prices = _ensure_numeric(btc_data)

    if len(prices) < 200:
        return {
            "trend": "unknown",
            "score": 0.0,
            "regime": "neutral",
            "sma_50": None,
            "sma_200": None,
            "sma_20": None,
            "alignment": "insufficient_data",
        }

    current = float(prices[-1])
    sma_50 = float(_sma(prices, 50)[-1]) if len(prices) >= 50 else None
    sma_200 = float(_sma(prices, 200)[-1])
    sma_20 = float(_sma(prices, 20)[-1]) if len(prices) >= 20 else None

    # Position relative to 50 and 200 SMAs
    above_50 = sma_50 is not None and current > sma_50
    above_200 = current > sma_200

    # 20 vs 50 alignment
    twenty_above_fifty = (sma_20 is not None and sma_50 is not None and sma_20 > sma_50)

    # Score: +1 for each bullish signal, -1 for each bearish
    score = 0.0
    if sma_50 is not None:
        score += 0.4 if above_50 else -0.4
    score += 0.3 if above_200 else -0.3
    if sma_20 is not None and sma_50 is not None:
        score += 0.3 if twenty_above_fifty else -0.3

    # Normalize to [-1, 1]
    score = max(-1.0, min(1.0, score))

    if score >= 0.3:
        trend = "bullish"
        regime = "risk_on"
    elif score <= -0.3:
        trend = "bearish"
        regime = "risk_off"
    else:
        trend = "sideways"
        regime = "neutral"

    if twenty_above_fifty:
        alignment = "aligned_bullish"
    elif sma_50 is not None and sma_20 is not None and sma_20 < sma_50:
        alignment = "aligned_bearish"
    else:
        alignment = "mixed"

    return {
        "trend": trend,
        "score": score,
        "regime": regime,
        "sma_50": sma_50,
        "sma_200": sma_200,
        "sma_20": sma_20,
        "alignment": alignment,
    }


# ---------------------------------------------------------------------------
# Component: cross-sectional funding dispersion
# ---------------------------------------------------------------------------

def _compute_funding_dispersion(funding_rates: Dict[str, float]) -> Dict[str, Any]:
    """
    Compute cross-sectional standard deviation of funding rates across coins.
    High dispersion = regime uncertainty, positioning disagreements.

    Args:
        funding_rates: dict of {symbol: funding_rate_decimal} across the universe.

    Returns:
        dict with {dispersion, mean, n_symbols, regime}.
    """
    rates = [v for v in funding_rates.values() if np.isfinite(v)]

    if len(rates) < 3:
        return {
            "dispersion": 0.0,
            "mean": 0.0,
            "n_symbols": len(rates),
            "regime": "unknown",
        }

    mean = float(statistics.mean(rates))
    if len(rates) >= 2:
        disp = float(statistics.stdev(rates))
    else:
        disp = 0.0

    # Thresholds: low < 0.0005 (0.05%), high > 0.002 (0.2%)
    if disp < 0.0005:
        regime = "low_dispersion"
    elif disp > 0.002:
        regime = "high_dispersion"
    else:
        regime = "moderate_dispersion"

    return {
        "dispersion": disp,
        "mean": mean,
        "n_symbols": len(rates),
        "regime": regime,
    }


# ---------------------------------------------------------------------------
# Component: aggregate OI trend
# ---------------------------------------------------------------------------

def _compute_oi_trend(oi_history: np.ndarray) -> Dict[str, Any]:
    """
    Compute aggregate open-interest trend over available history.

    Args:
        oi_history: 1-D array of aggregate OI values (newest last).

    Returns:
        dict with {trend, change_pct, regime}.
    """
    oi = _ensure_numeric(oi_history)

    if len(oi) < 5:
        return {
            "trend": "unknown",
            "change_pct": 0.0,
            "regime": "neutral",
        }

    # Use last 20% or min 5, max 30 bars for the trend window
    window = max(5, min(30, len(oi) // 5))
    recent = oi[-window:]
    earlier = oi[-(window * 2):-window] if len(oi) >= window * 2 else oi[:window]

    recent_avg = float(np.mean(recent))
    earlier_avg = float(np.mean(earlier))

    if earlier_avg == 0:
        change_pct = 0.0
    else:
        change_pct = float((recent_avg - earlier_avg) / earlier_avg)

    if change_pct > 0.05:
        trend = "expanding"
        regime = "risk_on"
    elif change_pct < -0.05:
        trend = "contracting"
        regime = "risk_off"
    else:
        trend = "flat"
        regime = "neutral"

    return {
        "trend": trend,
        "change_pct": change_pct,
        "regime": regime,
    }


# ---------------------------------------------------------------------------
# Component: stablecoin net flow
# ---------------------------------------------------------------------------

def _compute_stablecoin_flow(stablecoin_data: np.ndarray) -> Dict[str, Any]:
    """
    Compute net stablecoin inflow/outflow as a liquidity signal.

    Args:
        stablecoin_data: 1-D array of stablecoin supply or exchange balance (newest last).
            Positive deltas represent inflows; negative deltas represent outflows.

    Returns:
        dict with {flow, net_change_pct, regime}.
    """
    supply = _ensure_numeric(stablecoin_data)

    if len(supply) < 5:
        return {
            "flow": "unknown",
            "net_change_pct": 0.0,
            "regime": "neutral",
        }

    window = max(5, min(30, len(supply) // 5))
    recent = supply[-window:]
    earlier = supply[-(window * 2):-window] if len(supply) >= window * 2 else supply[:window]

    recent_avg = float(np.mean(recent))
    earlier_avg = float(np.mean(earlier))

    if earlier_avg == 0:
        net_change_pct = 0.0
    else:
        net_change_pct = float((recent_avg - earlier_avg) / earlier_avg)

    if net_change_pct > 0.03:
        flow = "inflow"
        regime = "risk_on"
    elif net_change_pct < -0.03:
        flow = "outflow"
        regime = "risk_off"
    else:
        flow = "neutral"
        regime = "neutral"

    return {
        "flow": flow,
        "net_change_pct": net_change_pct,
        "regime": regime,
    }


# ---------------------------------------------------------------------------
# Component: volatility regime
# ---------------------------------------------------------------------------

def _compute_volatility_regime(btc_data: np.ndarray, window: int = 30) -> Dict[str, Any]:
    """
    Compute current realised volatility percentile vs 1-year history.

    Args:
        btc_data: 1-D array of BTC closing prices (newest last).
        window: rolling lookback for current vol estimate.

    Returns:
        dict with {current_vol, vol_percentile, regime}.
    """
    prices = _ensure_numeric(btc_data)

    if len(prices) < window + 2:
        return {
            "current_vol": 0.0,
            "vol_percentile": 0.5,
            "regime": "unknown",
        }

    # Compute log returns
    log_returns = np.diff(np.log(prices))

    # Current vol: std of last `window` returns
    current_returns = log_returns[-window:]
    if len(current_returns) < 2:
        current_vol = 0.0
    else:
        current_vol = float(np.std(current_returns, ddof=1))

    # Rolling vol history: compute vol for each trailing window of same size
    rolling_vols = []
    for i in range(window, len(log_returns)):
        rw = log_returns[i - window:i]
        if len(rw) >= 2:
            rolling_vols.append(float(np.std(rw, ddof=1)))

    if not rolling_vols:
        return {
            "current_vol": current_vol,
            "vol_percentile": 0.5,
            "regime": "neutral",
        }

    # Percentile of current vol in rolling history
    vol_percentile = float(np.mean(np.array(rolling_vols) < current_vol))

    # High vol (>80th %ile) = risk_off for crypto (vol typically spikes in selloffs)
    if vol_percentile >= 0.80:
        regime = "risk_off"
    elif vol_percentile <= 0.20:
        regime = "risk_on"
    else:
        regime = "neutral"

    return {
        "current_vol": current_vol,
        "vol_percentile": vol_percentile,
        "regime": regime,
    }


# ---------------------------------------------------------------------------
# Main: get_regime
# ---------------------------------------------------------------------------

def get_regime(
    as_of: Optional[str] = None,
    asset_class: str = "crypto",
    btc_data: Optional[np.ndarray] = None,
    funding_rates: Optional[Dict[str, float]] = None,
    oi_history: Optional[np.ndarray] = None,
    stablecoin_data: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """
    Determine the current crypto market regime.

    Args:
        as_of: ISO timestamp for data freshness (ignored in computation,
               returned for compatibility).
        asset_class: must be 'crypto'; included for interface compatibility.
        btc_data: BTC closing price array (newest last).
        funding_rates: dict of {symbol: funding_rate_decimal}.
        oi_history: aggregate OI array (newest last).
        stablecoin_data: stablecoin supply/balance array (newest last).

    Returns:
        dict with overall regime assessment and all component signals.
    """
    timestamp = (_now_iso() if as_of is None else as_of)

    # Treat empty arrays/dicts as absent
    if _is_absent(btc_data):
        btc_data = None
    if _is_absent(oi_history):
        oi_history = None
    if _is_absent(stablecoin_data):
        stablecoin_data = None
    if _is_absent(funding_rates):
        funding_rates = None

    # If no data provided, return neutral/degraded result
    if btc_data is None and funding_rates is None and oi_history is None and stablecoin_data is None:
        return {
            "overall": "neutral",
            "confidence": 0.0,
            "stock_regime": "neutral",
            "crypto_regime": "neutral",
            "components": {
                "btc_trend": {"trend": "unknown", "score": 0.0, "regime": "neutral"},
                "funding_dispersion": {"dispersion": 0.0, "mean": 0.0, "n_symbols": 0, "regime": "unknown"},
                "oi_trend": {"trend": "unknown", "change_pct": 0.0, "regime": "neutral"},
                "stablecoin_flow": {"flow": "unknown", "net_change_pct": 0.0, "regime": "neutral"},
                "volatility_regime": {"current_vol": 0.0, "vol_percentile": 0.5, "regime": "neutral"},
            },
            "data_freshness": timestamp,
            "timestamp": timestamp,
        }

    # Compute component signals
    btc_trend = _compute_btc_trend(btc_data) if btc_data is not None else {
        "trend": "unknown", "score": 0.0, "regime": "neutral",
        "sma_50": None, "sma_200": None, "sma_20": None, "alignment": "insufficient_data",
    }

    funding_disp = _compute_funding_dispersion(funding_rates) if funding_rates is not None else {
        "dispersion": 0.0, "mean": 0.0, "n_symbols": 0, "regime": "unknown",
    }

    oi_trend = _compute_oi_trend(oi_history) if oi_history is not None else {
        "trend": "unknown", "change_pct": 0.0, "regime": "neutral",
    }

    stablecoin = _compute_stablecoin_flow(stablecoin_data) if stablecoin_data is not None else {
        "flow": "unknown", "net_change_pct": 0.0, "regime": "neutral",
    }

    vol_regime_data = _compute_volatility_regime(btc_data) if btc_data is not None else {
        "current_vol": 0.0, "vol_percentile": 0.5, "regime": "neutral",
    }

    # Count how many components provided signal
    n_signals = 0
    n_total = 0

    # Vote on regime (risk_on / risk_off / neutral)
    votes = {"risk_on": 0, "risk_off": 0, "neutral": 0}

    for comp, data in [
        ("btc_trend", btc_trend),
        ("oi_trend", oi_trend),
        ("stablecoin_flow", stablecoin),
    ]:
        n_total += 1
        reg = data.get("regime", "neutral")
        if reg in ("risk_on", "risk_off"):
            n_signals += 1
        # Map any unexpected regime values to "neutral"
        if reg not in votes:
            reg = "neutral"
        votes[reg] += 1

    # Volatility regime
    n_total += 1
    vol_reg = vol_regime_data.get("regime", "neutral")
    if vol_reg in ("risk_on", "risk_off"):
        n_signals += 1
    if vol_reg not in votes:
        vol_reg = "neutral"
    votes[vol_reg] += 1

    # Determine overall regime based on voting
    max_votes = max(votes.values())
    if max_votes == votes["risk_on"] and votes["risk_on"] > votes["risk_off"]:
        overall = "risk_on"
    elif max_votes == votes["risk_off"] and votes["risk_off"] > votes["risk_on"]:
        overall = "risk_off"
    elif votes["risk_on"] == votes["risk_off"] and votes["risk_on"] >= 2:
        overall = "caution"
    else:
        overall = "neutral"

    # Confidence: fraction of non-neutral signals
    confidence = (n_signals / max(1, n_total)) if n_total > 0 else 0.0
    confidence = min(1.0, max(0.0, confidence))

    # Funding dispersion modulates: high dispersion reduces confidence
    if funding_disp.get("regime") == "high_dispersion":
        confidence *= 0.8

    return {
        "overall": overall,
        "confidence": confidence,
        "stock_regime": overall,  # mirror for compatibility
        "crypto_regime": overall,
        "components": {
            "btc_trend": btc_trend,
            "funding_dispersion": funding_disp,
            "oi_trend": oi_trend,
            "stablecoin_flow": stablecoin,
            "volatility_regime": vol_regime_data,
        },
        "data_freshness": timestamp,
        "timestamp": timestamp,
    }


# ---------------------------------------------------------------------------
# tag_signal: mutates signal dict in-place with regime fields
# ---------------------------------------------------------------------------

def tag_signal(signal: Dict[str, Any], regime: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Mutate a signal dict in-place with regime annotation fields.

    Args:
        signal: signal dict to annotate (mutated in-place).
        regime: regime dict from get_regime(). If None, calls get_regime() internally.

    Returns:
        The same signal dict (mutated in-place) with added fields:
        regime, regime_confidence, regime_compatible, regime_action,
        regime_risk_multiplier.
    """
    if regime is None:
        regime = get_regime()

    overall = regime.get("overall", "neutral")
    confidence = regime.get("confidence", 0.0)

    # Determine compatibility and action
    if confidence < 0.3:
        compatible = "unknown"
        action = "caution"
        risk_multiplier = 0.5
    elif overall == "risk_on":
        compatible = True
        action = "normal"
        risk_multiplier = 1.0
    elif overall == "risk_off":
        compatible = True  # strategies may be short-biased
        action = "reduce"
        risk_multiplier = 0.5
    elif overall == "caution":
        compatible = True
        action = "caution"
        risk_multiplier = 0.5
    else:  # neutral
        compatible = True
        action = "normal"
        risk_multiplier = 1.0

    if confidence == 0.0:
        compatible = "unknown"

    signal["regime"] = overall
    signal["regime_confidence"] = confidence
    signal["regime_compatible"] = compatible
    signal["regime_action"] = action
    signal["regime_risk_multiplier"] = risk_multiplier

    return signal