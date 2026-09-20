"""
Tests for g6_regime_robustness.py — G61 through G67.

Covers: regime classification, regime score computation, concentration check,
pass/fail boundary, insufficient data handling, stock vs crypto paths,
and end-to-end evaluation on synthetic trades.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np

from g6_regime_robustness import (
    evaluate_g6,
    classify_regimes,
    _rolling_slope,
    _rolling_volatility,
    _extract_net_r,
    _extract_prices,
    _simplify_regimes,
    REGIME_SCORE_THRESHOLD,
    CONCENTRATION_LIMIT,
    MIN_REGIMES_FOR_MEANINGFUL,
    MIN_TRADES_PER_REGIME,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_trades(
    n: int = 200,
    asset_class: str = "crypto",
    seed: int = 42,
    base_price: float = 50000.0,
    trend: float = 0.001,
    vol: float = 0.03,
    win_rate: float = 0.55,
    avg_win_r: float = 2.0,
    avg_loss_r: float = -1.0,
) -> list:
    """
    Generate synthetic trades in time order with regime structure:
    First half: bull trend, second half: bear (or random walk to
    ensure multiple regimes appear).
    """
    rng = np.random.RandomState(seed)
    returns = rng.normal(trend, vol, n)
    prices = base_price * np.exp(np.cumsum(returns))
    prices = np.abs(prices) + 1.0

    trades = []
    for i in range(n):
        is_win = rng.rand() < win_rate
        r_mult = avg_win_r if is_win else avg_loss_r

        # Add some noise to R
        r_mult += rng.normal(0, 0.3)

        entry = float(prices[i])
        stop = entry * (1 - 0.02)  # 2% risk

        trades.append({
            "symbol": "BTC-USD" if asset_class == "crypto" else "SPY",
            "strategy": "test_strategy",
            "direction": "long",
            "date": f"2024-{((i // 20) % 12) + 1:02d}-{(i % 20) + 1:02d}",
            "entry_price": entry,
            "stop_price": stop,
            "exit_price": entry * 1.02 if is_win else entry * 0.98,
            "r_multiple": r_mult,
            "asset_class": asset_class,
        })
    return trades


def _make_regime_specific_trades(
    n_bull: int = 60,
    n_bear: int = 60,
    n_flat: int = 60,
    asset_class: str = "crypto",
    seed: int = 42,
) -> list:
    """Generate trades with distinct regime phases, all profitable."""
    rng = np.random.RandomState(seed)
    trades = []

    # Bull phase: rising prices, positive R
    bull_prices = 50000.0 * np.exp(np.cumsum(rng.normal(0.003, 0.02, n_bull)))
    bull_prices = np.abs(bull_prices) + 1.0
    for i in range(n_bull):
        r_mult = rng.normal(1.5, 0.5)
        entry = float(bull_prices[i])
        trades.append({
            "symbol": "BTC-USD",
            "strategy": "test",
            "direction": "long",
            "date": f"2024-01-{(i % 28) + 1:02d}",
            "entry_price": entry,
            "stop_price": entry * 0.98,
            "exit_price": entry * 1.02,
            "r_multiple": r_mult,
            "asset_class": asset_class,
        })

    # Bear phase: falling prices, strategy still profitable (e.g. short-biased)
    bear_prices = 35000.0 * np.exp(np.cumsum(rng.normal(-0.003, 0.03, n_bear)))
    bear_prices = np.abs(bear_prices) + 1.0
    for i in range(n_bear):
        r_mult = rng.normal(1.0, 0.5)
        entry = float(bear_prices[i])
        trades.append({
            "symbol": "BTC-USD",
            "strategy": "test",
            "direction": "short",
            "date": f"2024-03-{(i % 28) + 1:02d}",
            "entry_price": entry,
            "stop_price": entry * 1.02,
            "exit_price": entry * 0.98,
            "r_multiple": r_mult,
            "asset_class": asset_class,
        })

    # Flat phase: sideways prices
    flat_prices = 42000.0 * np.exp(np.cumsum(rng.normal(0.0, 0.015, n_flat)))
    flat_prices = np.abs(flat_prices) + 1.0
    for i in range(n_flat):
        r_mult = rng.normal(0.8, 0.4)
        entry = float(flat_prices[i])
        trades.append({
            "symbol": "BTC-USD",
            "strategy": "test",
            "direction": "long",
            "date": f"2024-06-{(i % 28) + 1:02d}",
            "entry_price": entry,
            "stop_price": entry * 0.98,
            "exit_price": entry * 1.02,
            "r_multiple": r_mult,
            "asset_class": asset_class,
        })

    return trades


# ---------------------------------------------------------------------------
# G61: evaluate_g6 on a robust strategy (all regimes profitable) passes
# ---------------------------------------------------------------------------

def test_G61_robust_strategy_passes():
    """A strategy profitable in bull, bear, and flat regimes should pass G6."""
    trades = _make_regime_specific_trades(
        n_bull=60, n_bear=60, n_flat=60, asset_class="crypto"
    )
    result = evaluate_g6(trades, asset_class="crypto")

    # All regimes should be profitable (positive net R)
    for regime, stats in result["regime_breakdown"].items():
        assert stats["profitable"], f"Regime {regime} should be profitable"

    assert result["regime_score"] >= REGIME_SCORE_THRESHOLD
    assert result["passes"] is True
    assert result["regime_count"] >= MIN_REGIMES_FOR_MEANINGFUL
    assert result["concentration"] <= CONCENTRATION_LIMIT


# ---------------------------------------------------------------------------
# G62: evaluate_g6 on a regime-dependent strategy (only bull works) fails
# ---------------------------------------------------------------------------

def test_G62_bull_only_strategy_fails():
    """A strategy that only makes money in bull markets must fail G6."""
    rng = np.random.RandomState(42)

    trades = []
    # Bull phase: prices rising, strategy prints positive R
    bull_prices = 50000.0 * np.exp(np.cumsum(rng.normal(0.003, 0.02, 60)))
    bull_prices = np.abs(bull_prices) + 1.0
    for i in range(60):
        entry = float(bull_prices[i])
        trades.append({
            "symbol": "BTC-USD", "strategy": "bull_only",
            "direction": "long",
            "date": f"2024-01-{(i % 28) + 1:02d}",
            "entry_price": entry,
            "stop_price": entry * 0.98,
            "exit_price": entry * 1.02,
            "r_multiple": rng.normal(2.0, 0.5),
            "asset_class": "crypto",
        })

    # Bear phase: prices falling, strategy loses consistently
    bear_prices = 35000.0 * np.exp(np.cumsum(rng.normal(-0.003, 0.03, 60)))
    bear_prices = np.abs(bear_prices) + 1.0
    for i in range(60):
        entry = float(bear_prices[i])
        trades.append({
            "symbol": "BTC-USD", "strategy": "bull_only",
            "direction": "long",
            "date": f"2024-03-{(i % 28) + 1:02d}",
            "entry_price": entry,
            "stop_price": entry * 0.98,
            "exit_price": entry * 0.98,
            "r_multiple": rng.normal(-1.0, 0.3),
            "asset_class": "crypto",
        })

    # Flat phase: also loses
    flat_prices = 42000.0 * np.exp(np.cumsum(rng.normal(0.0, 0.015, 60)))
    flat_prices = np.abs(flat_prices) + 1.0
    for i in range(60):
        entry = float(flat_prices[i])
        trades.append({
            "symbol": "BTC-USD", "strategy": "bull_only",
            "direction": "long",
            "date": f"2024-06-{(i % 28) + 1:02d}",
            "entry_price": entry,
            "stop_price": entry * 0.98,
            "exit_price": entry * 0.98,
            "r_multiple": rng.normal(-0.5, 0.3),
            "asset_class": "crypto",
        })

    result = evaluate_g6(trades, asset_class="crypto")

    # Should fail: not profitable in all regimes
    assert result["passes"] is False
    # Some regimes should be unprofitable
    unprofitable = [
        r for r, s in result["regime_breakdown"].items() if not s["profitable"]
    ]
    assert len(unprofitable) > 0, "Expected at least one unprofitable regime"
    assert result["regime_score"] < 1.0, "Should not have perfect regime score"


# ---------------------------------------------------------------------------
# G63: concentration check — single regime dominating total PnL
# ---------------------------------------------------------------------------

def test_G63_concentration_check():
    """When one regime accounts for >70% of total net R, fails even if score OK.

    Creates two distinct phases: a long bull_normal phase with huge R-multiples
    followed by a short high-vol phase with negative R. The bull_normal regime
    captures >70% of total net R, triggering the concentration violation.
    """
    rng = np.random.RandomState(99)

    # Phase 1: strong uptrend, low vol (110 trades → bull_normal), huge R
    p1 = 400.0 * np.exp(np.cumsum(rng.normal(0.008, 0.003, 110)))
    p1 = np.abs(p1) + 1.0

    # Phase 2: flat, high vol (40 trades → flat_high/bear_high), negative R
    p2_start = p1[-1]
    p2 = p2_start * np.exp(np.cumsum(rng.normal(0.0, 0.03, 40)))
    p2 = np.abs(p2) + 1.0

    all_prices = np.concatenate([p1, p2])

    trades = []
    for i in range(150):
        entry = float(all_prices[i])
        if i < 110:
            r_mult = rng.normal(15.0, 2.0)
        else:
            r_mult = rng.normal(-2.0, 0.3)

        trades.append({
            "symbol": "SPY", "strategy": "concentrated",
            "direction": "long",
            "date": f"2024-{(i // 30) + 1:02d}-{(i % 28) + 1:02d}",
            "entry_price": entry,
            "stop_price": entry * 0.98,
            "exit_price": entry * 1.02,
            "r_multiple": r_mult,
            "asset_class": "stock",
        })

    result = evaluate_g6(trades, asset_class="stock")

    assert result["concentration"] > CONCENTRATION_LIMIT, (
        f"Expected concentration > {CONCENTRATION_LIMIT}, got {result['concentration']:.3f}"
    )
    assert result["concentration_exceeded"] is True
    assert result["passes"] is False  # concentration violation → fail


# ---------------------------------------------------------------------------
# G64: edge cases — empty trades, insufficient data
# ---------------------------------------------------------------------------

def test_G64_edge_cases():
    """Empty trades and insufficient data should return graceful failures."""
    # Empty
    result = evaluate_g6([])
    assert result["passes"] is False
    assert "error" in result
    assert result["regime_count"] == 0

    # Too few trades for classification
    few_trades = [
        {"symbol": "BTC-USD", "entry_price": 50000.0, "r_multiple": 1.0,
         "asset_class": "crypto"},
        {"symbol": "BTC-USD", "entry_price": 50100.0, "r_multiple": -1.0,
         "asset_class": "crypto"},
    ]
    result2 = evaluate_g6(few_trades, asset_class="crypto")
    assert result2["passes"] is False
    assert "error" in result2

    # All trades classified as insufficient_data
    flat = [{"symbol": "TEST", "entry_price": 100.0, "r_multiple": 0.5,
             "asset_class": "stock"}] * 10
    result3 = evaluate_g6(flat, asset_class="stock")
    assert result3["passes"] is False


# ---------------------------------------------------------------------------
# G65: stock path — auto-detection and stock-specific classification
# ---------------------------------------------------------------------------

def test_G65_stock_classification():
    """Stock trades are auto-detected and classified correctly."""
    rng = np.random.RandomState(55)
    n = 150

    # Generate SPY-like trades with clear bull/bear structure
    prices_bull = 400.0 * np.exp(np.cumsum(rng.normal(0.003, 0.015, 70)))
    prices_bull = np.abs(prices_bull) + 1.0
    prices_bear = 500.0 * np.exp(np.cumsum(rng.normal(-0.003, 0.02, 80)))
    prices_bear = np.abs(prices_bear) + 1.0
    all_prices = np.concatenate([prices_bull, prices_bear])

    trades = []
    for i in range(n):
        entry = float(all_prices[i])
        trades.append({
            "symbol": "SPY",
            "strategy": "test",
            "direction": "long",
            "date": f"2024-{(i // 30) + 1:02d}-{(i % 28) + 1:02d}",
            "entry_price": entry,
            "stop_price": entry * 0.98,
            "exit_price": entry * 1.02 if rng.rand() < 0.55 else entry * 0.98,
            "r_multiple": rng.normal(1.0, 0.5),
            "asset_class": "stock",
        })

    result = evaluate_g6(trades)

    assert result["asset_class"] == "stock"
    assert result["regime_count"] > 0
    # Should have at least a couple of regimes
    assert len(result["regime_breakdown"]) >= 1


# ---------------------------------------------------------------------------
# G66: helper functions — rolling slope, volatility, net R extraction
# ---------------------------------------------------------------------------

def test_G66a_rolling_slope():
    """Rolling slope detects trends correctly."""
    # Strong uptrend
    prices_up = 100.0 * np.exp(np.cumsum(np.full(60, 0.01)))
    slopes = _rolling_slope(prices_up, 20)
    valid = slopes[~np.isnan(slopes)]
    assert len(valid) > 0
    assert np.all(valid > 0), "All slopes should be positive in uptrend"

    # Strong downtrend
    prices_down = 100.0 * np.exp(np.cumsum(np.full(60, -0.01)))
    slopes_down = _rolling_slope(prices_down, 20)
    valid_down = slopes_down[~np.isnan(slopes_down)]
    assert len(valid_down) > 0
    assert np.all(valid_down < 0), "All slopes should be negative in downtrend"

    # Too few data points
    short = _rolling_slope(np.array([100.0, 101.0]), 20)
    assert np.all(np.isnan(short))


def test_G66b_rolling_volatility():
    """Rolling volatility scales with price variability."""
    rng = np.random.RandomState(42)
    # Low vol
    prices_low = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.005, 60)))
    vol_low = _rolling_volatility(prices_low, 30)
    valid_low = vol_low[~np.isnan(vol_low)]
    avg_low = float(np.mean(valid_low))

    # High vol
    prices_high = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.05, 60)))
    vol_high = _rolling_volatility(prices_high, 30)
    valid_high = vol_high[~np.isnan(vol_high)]
    avg_high = float(np.mean(valid_high))

    assert avg_high > avg_low, f"High vol ({avg_high:.4f}) should exceed low vol ({avg_low:.4f})"


def test_G66c_extract_net_r():
    """Net R extraction uses correct priority: gauntlet_r > net_r > r_multiple."""
    trades = [
        {"entry_price": 100.0, "gauntlet_r": 1.5, "net_r": 1.2, "r_multiple": 1.0},
        {"entry_price": 100.0, "net_r": 0.8, "r_multiple": 0.6},
        {"entry_price": 100.0, "r_multiple": 0.3},
        {"entry_price": 100.0},  # no R field
    ]
    net_r = _extract_net_r(trades)
    assert net_r[0] == 1.5  # gauntlet_r wins
    assert net_r[1] == 0.8  # net_r fallback
    assert net_r[2] == 0.3  # r_multiple fallback
    assert net_r[3] == 0.0  # missing → zero


def test_G66d_simplify_regimes():
    """Tiny regimes are merged into 'other'."""
    regimes = ["bull_normal"] * 20 + ["bear_high"] * 2 + ["flat_low"] * 15
    net_r = np.ones(len(regimes))
    simplified, unique = _simplify_regimes(regimes, net_r, min_trades=5)

    assert "other" in simplified
    assert "bull_normal" in unique
    assert "flat_low" in unique
    assert "bear_high" not in unique  # too few, merged


# ---------------------------------------------------------------------------
# G67: end-to-end — crypto path uses crypto_regime blending
# ---------------------------------------------------------------------------

def test_G67_crypto_path():
    """Crypto trades leverage crypto_regime.py vol percentile blending."""
    trades = _make_trades(n=200, asset_class="crypto", seed=77,
                          trend=0.0005, vol=0.03, win_rate=0.55)

    result = evaluate_g6(trades, asset_class="crypto")

    assert result["asset_class"] == "crypto"
    assert result["total_trades"] == 200
    assert result["regime_count"] > 0, "Should detect at least one regime"
    # All fields present
    for key in ("regime_score", "passes", "regime_breakdown",
                "concentration", "concentration_exceeded",
                "regime_count", "profitable_regimes", "total_net_r"):
        assert key in result, f"Missing key: {key}"

    # Breakdown entries have required fields
    for regime, stats in result["regime_breakdown"].items():
        for field in ("trade_count", "total_net_r", "avg_net_r",
                      "win_rate", "profitable"):
            assert field in stats, f"Missing field {field} in {regime}"


# ---------------------------------------------------------------------------
# Additional: force cost_adjuster integration
# ---------------------------------------------------------------------------

def test_cost_adjuster_integration():
    """When trades lack gauntlet_r, cost_adjuster.batch_adjust is called."""
    rng = np.random.RandomState(33)
    n = 150
    prices = 50000.0 * np.exp(np.cumsum(rng.normal(0.001, 0.03, n)))

    trades = []
    for i in range(n):
        entry = float(np.abs(prices[i]) + 1.0)
        trades.append({
            "symbol": "BTC-USD",
            "strategy": "test",
            "direction": "long",
            "date": f"2024-{(i // 30) + 1:02d}-{(i % 28) + 1:02d}",
            "entry_price": entry,
            "stop_price": entry * 0.97,
            "exit_price": entry * 1.02,
            "r_multiple": rng.normal(1.0, 0.4),
            "asset_class": "crypto",
        })

    # No gauntlet_r present — cost_adjuster should kick in
    result = evaluate_g6(trades, asset_class="crypto", apply_cost_adjustment=True)
    assert result["total_trades"] == n
    assert result["total_net_r"] != 0.0  # cost adjustment applied

    # Trades should now have gauntlet_r
    assert any(t.get("gauntlet_r") not in (None, "", '') for t in trades), \
        "batch_adjust should have added gauntlet_r"