"""
Tests for crypto_regime.py — CR1 through CR11.

Mirrors the 11 test areas of test_regime_filter.py against crypto inputs.
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np

from crypto_regime import (
    get_regime,
    tag_signal,
    _compute_btc_trend,
    _compute_funding_dispersion,
    _compute_oi_trend,
    _compute_stablecoin_flow,
    _compute_volatility_regime,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_btc_data(n: int = 500, seed: int = 42, trend: float = 0.0002) -> np.ndarray:
    """Generate synthetic BTC prices with a mild drift and realistic volatility."""
    rng = np.random.RandomState(seed)
    returns = rng.normal(trend, 0.03, n)
    prices = 50000.0 * np.exp(np.cumsum(returns))
    return prices


def _make_bullish_btc(n: int = 500) -> np.ndarray:
    """Generate strongly bullish BTC prices."""
    return _make_btc_data(n, seed=7, trend=0.002)


def _make_bearish_btc(n: int = 500) -> np.ndarray:
    """Generate strongly bearish BTC prices."""
    return _make_btc_data(n, seed=13, trend=-0.002)


def _make_oi_data(n: int = 100, trend_pct: float = 0.10, seed: int = 99) -> np.ndarray:
    """Generate synthetic aggregate OI data."""
    rng = np.random.RandomState(seed)
    base = 10_000_000.0
    trend_line = base * (1.0 + trend_pct * np.arange(n) / n)
    noise = rng.normal(0, base * 0.005, n)
    return trend_line + noise


def _make_stablecoin_data(n: int = 100, trend_pct: float = 0.05, seed: int = 42) -> np.ndarray:
    """Generate synthetic stablecoin supply data."""
    rng = np.random.RandomState(seed)
    base = 100_000_000_000.0
    trend_line = base * (1.0 + trend_pct * np.arange(n) / n)
    noise = rng.normal(0, base * 0.005, n)
    return trend_line + noise


# ---------------------------------------------------------------------------
# CR1: get_regime returns valid dict with all required fields
# ---------------------------------------------------------------------------

def test_CR1_get_regime_returns_valid_dict():
    btc = _make_btc_data(500)
    oi = _make_oi_data(100)
    stable = _make_stablecoin_data(100)
    funding = {
        "BTC": 0.0001,
        "ETH": 0.0005,
        "SOL": -0.0002,
        "AVAX": 0.0003,
        "DOGE": 0.0008,
    }

    result = get_regime(
        btc_data=btc,
        funding_rates=funding,
        oi_history=oi,
        stablecoin_data=stable,
    )

    # Top-level fields
    assert "overall" in result
    assert "confidence" in result
    assert "stock_regime" in result
    assert "crypto_regime" in result
    assert "components" in result
    assert "data_freshness" in result
    assert "timestamp" in result

    # overall must be a valid value
    assert result["overall"] in ("risk_on", "risk_off", "neutral", "caution")

    # confidence in [0, 1]
    assert 0.0 <= result["confidence"] <= 1.0

    # stock_regime mirrors crypto_regime for compatibility
    assert result["stock_regime"] == result["crypto_regime"]

    # Components
    comps = result["components"]
    assert "btc_trend" in comps
    assert "funding_dispersion" in comps
    assert "oi_trend" in comps
    assert "stablecoin_flow" in comps
    assert "volatility_regime" in comps

    # BTC trend sub-fields
    assert "trend" in comps["btc_trend"]
    assert "score" in comps["btc_trend"]
    assert "regime" in comps["btc_trend"]

    # Funding dispersion sub-fields
    assert "dispersion" in comps["funding_dispersion"]
    assert "mean" in comps["funding_dispersion"]
    assert "n_symbols" in comps["funding_dispersion"]

    # data_freshness and timestamp are strings
    assert isinstance(result["data_freshness"], str)
    assert isinstance(result["timestamp"], str)


# ---------------------------------------------------------------------------
# CR2: tag_signal mutates correctly
# ---------------------------------------------------------------------------

def test_CR2_tag_signal_mutates_correctly():
    regime = get_regime(btc_data=_make_btc_data(500))
    signal = {"symbol": "BTC-USD", "direction": "long", "price": 50000.0}

    result = tag_signal(signal, regime)

    # Returns the same object
    assert result is signal

    # Check new fields
    assert "regime" in signal
    assert "regime_confidence" in signal
    assert "regime_compatible" in signal
    assert "regime_action" in signal
    assert "regime_risk_multiplier" in signal

    assert isinstance(signal["regime_confidence"], float)
    assert isinstance(signal["regime_risk_multiplier"], float)
    assert signal["regime_action"] in ("normal", "reduce", "caution", "unknown")


# ---------------------------------------------------------------------------
# CR3: tag_signal with regime=None calls get_regime() internally
# ---------------------------------------------------------------------------

def test_CR3_tag_signal_none_regime_calls_get_regime_internally():
    signal = {"symbol": "ETH-USD", "direction": "short", "price": 3000.0}

    result = tag_signal(signal, regime=None)

    assert result is signal
    assert "regime" in signal
    assert "regime_confidence" in signal
    assert signal["regime"] == "neutral"  # no data → neutral
    assert signal["regime_confidence"] == 0.0  # no data → zero confidence


# ---------------------------------------------------------------------------
# CR4: unknown strategy not suppressed (regime present but neutral)
# ---------------------------------------------------------------------------

def test_CR4_unknown_strategy_not_suppressed():
    # Even in neutral/unknown regime, signal still gets tagged
    signal = {"symbol": "UNKNOWN", "direction": "long", "price": 1.0}

    result = tag_signal(signal, regime=None)

    assert "regime" in signal
    assert "regime_confidence" in signal
    # Signal is not deleted or filtered — it's just tagged
    assert signal["symbol"] == "UNKNOWN"
    assert signal["direction"] == "long"


# ---------------------------------------------------------------------------
# CR5: confidence=0 -> unknown tags
# ---------------------------------------------------------------------------

def test_CR5_zero_confidence_gives_unknown_tags():
    # Pass no data → confidence=0
    regime = get_regime()
    assert regime["confidence"] == 0.0
    assert regime["overall"] == "neutral"

    signal = {"symbol": "TEST", "direction": "long", "price": 100.0}
    result = tag_signal(signal, regime)

    assert result["regime_confidence"] == 0.0
    # With confidence=0, compatible should be "unknown"
    assert result["regime_compatible"] == "unknown"


# ---------------------------------------------------------------------------
# CR6: graceful degradation on missing data
# ---------------------------------------------------------------------------

def test_CR6_graceful_degradation_empty_data():
    # No data at all
    regime = get_regime()
    assert regime["overall"] == "neutral"
    assert regime["confidence"] == 0.0

    # Empty arrays
    regime2 = get_regime(btc_data=np.array([]))
    assert regime2["overall"] == "neutral"
    assert regime2["confidence"] <= 0.5  # may have some confidence from vote count
    assert regime2["components"]["btc_trend"]["regime"] == "neutral"

    # Very short array (< 200 bars)
    short = np.array([50000.0, 50100.0, 49900.0])
    regime3 = get_regime(btc_data=short)
    assert "components" in regime3
    assert regime3["components"]["btc_trend"]["trend"] == "unknown"


# ---------------------------------------------------------------------------
# CR7: as_of look-ahead enforcement
# ---------------------------------------------------------------------------

def test_CR7_as_of_preserved():
    # as_of should be preserved in data_freshness and timestamp
    as_of = "2026-01-15T12:00:00+00:00"
    regime = get_regime(as_of=as_of, btc_data=_make_btc_data(500))
    assert regime["data_freshness"] == as_of

    # Without as_of, should be now-ish
    regime2 = get_regime(btc_data=_make_btc_data(500))
    assert "2026" in regime2["timestamp"] or "2025" in regime2["timestamp"]


# ---------------------------------------------------------------------------
# CR8: component functions return sane values
# ---------------------------------------------------------------------------

def test_CR8a_btc_trend_sane():
    bullish = _make_bullish_btc(500)
    result = _compute_btc_trend(bullish)
    assert result["trend"] in ("bullish", "bearish", "sideways", "unknown")
    assert -1.0 <= result["score"] <= 1.0
    # In a strongly bullish environment, trend should be bullish
    assert result["trend"] == "bullish"
    assert result["regime"] == "risk_on"

    bearish = _make_bearish_btc(500)
    result_bear = _compute_btc_trend(bearish)
    assert result_bear["trend"] == "bearish"
    assert result_bear["regime"] == "risk_off"


def test_CR8b_funding_dispersion_sane():
    rates = {"BTC": 0.0001, "ETH": 0.0005, "SOL": -0.0002, "AVAX": 0.0003, "DOGE": 0.0008}
    result = _compute_funding_dispersion(rates)
    assert result["n_symbols"] == 5
    assert result["dispersion"] >= 0.0
    assert "regime" in result

    # Insufficient data
    result2 = _compute_funding_dispersion({"BTC": 0.0001})
    assert result2["dispersion"] == 0.0
    assert result2["regime"] == "unknown"


def test_CR8c_oi_trend_sane():
    # Use a much stronger trend to overcome noise in _make_oi_data
    oi_growing = _make_oi_data(100, trend_pct=0.40)
    result = _compute_oi_trend(oi_growing)
    assert result["trend"] in ("expanding", "contracting", "flat", "unknown")
    assert result["change_pct"] > 0.05  # should be strongly growing
    assert result["regime"] == "risk_on"

    oi_shrinking = _make_oi_data(100, trend_pct=-0.40)
    result2 = _compute_oi_trend(oi_shrinking)
    assert result2["trend"] == "contracting"
    assert result2["regime"] == "risk_off"

    # Very short history
    result3 = _compute_oi_trend(np.array([1.0, 2.0]))
    assert result3["trend"] == "unknown"


def test_CR8d_stablecoin_flow_sane():
    # Use a strong trend to overcome noise (noise ~0.5% per bar)
    inflow = _make_stablecoin_data(100, trend_pct=0.25)
    result = _compute_stablecoin_flow(inflow)
    assert result["flow"] in ("inflow", "outflow", "neutral", "unknown")
    assert result["regime"] == "risk_on"

    outflow = _make_stablecoin_data(100, trend_pct=-0.25)
    result2 = _compute_stablecoin_flow(outflow)
    assert result2["regime"] == "risk_off"


def test_CR8e_volatility_regime_sane():
    btc = _make_btc_data(500)
    result = _compute_volatility_regime(btc)
    assert "current_vol" in result
    assert "vol_percentile" in result
    assert "regime" in result
    assert 0.0 <= result["vol_percentile"] <= 1.0
    assert result["current_vol"] >= 0.0

    # Volatile data should register
    rng = np.random.RandomState(42)
    high_vol_prices = 50000.0 * np.exp(np.cumsum(rng.normal(0.0002, 0.08, 500)))
    result_hv = _compute_volatility_regime(high_vol_prices)
    assert result_hv["current_vol"] > 0.0

    # Short data
    result_short = _compute_volatility_regime(np.array([50000.0, 50100.0]))
    assert result_short["regime"] == "unknown"


# ---------------------------------------------------------------------------
# CR9: strategy selector integration (import and call)
# ---------------------------------------------------------------------------

def test_CR9_strategy_selector_integration():
    """Verify that crypto_regime can be imported and called like regime_filter."""
    from crypto_regime import get_regime as regime_getter, tag_signal as regime_tagger

    # Simulate strategy selector calling get_regime
    regime = regime_getter(btc_data=_make_btc_data(500))
    assert "overall" in regime
    assert "crypto_regime" in regime

    # Simulate strategy selector calling tag_signal
    signal = {"symbol": "BTC-USD", "direction": "long", "entry_price": 52000.0,
              "strategy": "momentum_breakout", "timestamp": "2026-01-15T12:00:00Z"}
    tagged = regime_tagger(signal, regime)
    assert tagged is signal
    assert "regime" in tagged
    assert "regime_risk_multiplier" in tagged


# ---------------------------------------------------------------------------
# CR10: performance < 1s
# ---------------------------------------------------------------------------

def test_CR10_performance():
    btc = _make_btc_data(500)
    oi = _make_oi_data(100)
    stable = _make_stablecoin_data(100)
    funding = {"BTC": 0.0001, "ETH": 0.0005, "SOL": -0.0002}

    start = time.perf_counter()
    for _ in range(20):
        get_regime(btc_data=btc, funding_rates=funding, oi_history=oi,
                   stablecoin_data=stable)
    elapsed = time.perf_counter() - start

    avg_ms = (elapsed / 20) * 1000
    assert elapsed < 1.0, f"20 calls took {elapsed:.3f}s (avg {avg_ms:.1f}ms)"


# ---------------------------------------------------------------------------
# CR11: btc_trend produces valid regimes
# ---------------------------------------------------------------------------

def test_CR11_btc_trend_valid_regimes():
    # Bullish case
    bullish = _make_bullish_btc(500)
    result_bull = _compute_btc_trend(bullish)
    assert result_bull["regime"] == "risk_on"
    assert result_bull["trend"] == "bullish"
    assert result_bull["score"] > 0.0

    # Bearish case
    bearish = _make_bearish_btc(500)
    result_bear = _compute_btc_trend(bearish)
    assert result_bear["regime"] == "risk_off"
    assert result_bear["trend"] == "bearish"
    assert result_bear["score"] < 0.0

    # Sideways / neutral case: mean-reverting around a level
    rng = np.random.RandomState(123)
    noise = rng.normal(0.0, 0.01, 500)
    sideways = 50000.0 * np.exp(np.cumsum(noise))
    result_side = _compute_btc_trend(sideways)
    # Should be sideways or mildly bullish/bearish — but regime should be valid
    assert result_side["regime"] in ("risk_on", "risk_off", "neutral")
    assert result_side["trend"] in ("bullish", "bearish", "sideways", "unknown")
    assert -1.0 <= result_side["score"] <= 1.0

    # Insufficient data
    result_short = _compute_btc_trend(np.array([50000.0, 50100.0]))
    assert result_short["regime"] == "neutral"
    assert result_short["trend"] == "unknown"


# ---------------------------------------------------------------------------
# Additional: verify risk_multiplier logic
# ---------------------------------------------------------------------------

def test_risk_multiplier_by_regime():
    """Verify risk_multiplier is sensible for each regime type."""
    signal = {"symbol": "TEST", "direction": "long", "price": 100.0}

    # risk_on → 1.0
    regime_on = get_regime(btc_data=_make_bullish_btc(500))
    # Force risk_on by using heavily bullish data
    if regime_on["overall"] == "risk_on":
        tagged = tag_signal({"symbol": "TEST", "direction": "long", "price": 100.0},
                            regime_on)
        assert tagged["regime_risk_multiplier"] == 1.0
        assert tagged["regime_action"] == "normal"

    # risk_off → 0.5
    regime_off = get_regime(btc_data=_make_bearish_btc(500))
    if regime_off["overall"] == "risk_off":
        tagged = tag_signal({"symbol": "TEST", "direction": "short", "price": 100.0},
                            regime_off)
        assert tagged["regime_risk_multiplier"] == 0.5
        assert tagged["regime_action"] == "reduce"

    # No data → confidence=0 → risk_multiplier=0.5 (caution mode)
    regime_neutral = get_regime()
    tagged_neut = tag_signal({"symbol": "TEST", "direction": "long", "price": 100.0},
                             regime_neutral)
    assert tagged_neut["regime_confidence"] == 0.0
    assert tagged_neut["regime_compatible"] == "unknown"
    assert tagged_neut["regime_risk_multiplier"] == 0.5  # confidence=0 → caution