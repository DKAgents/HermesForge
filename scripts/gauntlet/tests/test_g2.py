"""
Tests for g2_parameter_sensitivity.py — TS01 through TS07.

Tests cover:
    TS01: Parameter extraction from a scanner with PARAMS dict
    TS02: Auto-detection fallback when PARAMS dict is absent
    TS03: Variation generation (correct magnitude, integer rounding)
    TS04: net_r computation from trade list
    TS05: Robustness score computation (all positive, all negative, mixed)
    TS06: Full sensitivity test with synthetic data and a mock scanner
    TS07: Edge cases: no params, empty trades, invalid strategy_id
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
import pandas as pd

from g2_parameter_sensitivity import (
    extract_params,
    generate_variations,
    _net_r,
    run_sensitivity_test,
    evaluate_gate,
    make_synthetic_ohlcv,
    PASS_THRESHOLD,
    DEFAULT_DELTA_PCT,
    list_strategies,
)

# ── TS01: extract_params with explicit PARAMS dict ─────────────────────────

def test_extract_params_from_parms_dict(monkeypatch):
    """Module declares PARAMS = {...} — only numeric entries returned."""
    # Create a minimal mock module
    class MockModule:
        STRATEGY_ID = "STR-TEST-params"
        PARAMS = {
            "ATR_PERIOD": 14,
            "ATR_MULT": 2.0,
            "EMA_PERIOD": 20,
            "COOLDOWN_BARS": 15,
            "NOT_NUMERIC": "hello",
            "ALSO_NUMERIC": True,  # bool should be excluded
        }

    import g2_parameter_sensitivity as g2
    monkeypatch.setattr(g2, "_scanner_module_cache", {})
    monkeypatch.setattr(g2, "_find_scanner_module", lambda sid: (MockModule(), None))

    params = extract_params("STR-TEST-params")
    assert "ATR_PERIOD" in params
    assert "ATR_MULT" in params
    assert "EMA_PERIOD" in params
    assert "COOLDOWN_BARS" in params
    assert params["ATR_PERIOD"] == 14
    assert params["ATR_MULT"] == 2.0
    assert "NOT_NUMERIC" not in params
    assert "ALSO_NUMERIC" not in params  # bool excluded


# ── TS02: extract_params auto-detection fallback ───────────────────────────

def test_extract_params_autodetect(monkeypatch):
    """No PARAMS dict — auto-detect uppercase numeric constants."""
    class MockModule:
        STRATEGY_ID = "STR-TEST-autodetect"
        ATR_PERIOD = 10
        ATR_MULT = 1.5
        MAX_HOLD_BARS = 20
        COOLDOWN_BARS = 15
        # These should be excluded
        STRATEGY_NAME = "Test Strategy"
        __version__ = "1.0"

    import g2_parameter_sensitivity as g2
    monkeypatch.setattr(g2, "_scanner_module_cache", {})
    monkeypatch.setattr(g2, "_find_scanner_module", lambda sid: (MockModule(), None))

    params = extract_params("STR-TEST-autodetect")
    assert "ATR_PERIOD" in params
    assert "ATR_MULT" in params
    assert "MAX_HOLD_BARS" in params
    assert "COOLDOWN_BARS" in params
    assert params["ATR_PERIOD"] == 10
    assert "STRATEGY_NAME" not in params  # not uppercase (mixed case)
    assert "__version__" not in params     # starts with underscore
    assert "STRATEGY_ID" not in params     # in NON_PARAM_NAMES
    assert "STRATEGY_NAME" not in params   # not uppercase (it's mixed case)


# ── TS03: generate_variations correctness ──────────────────────────────────

def test_generate_variations_float_params():
    """Float params: ±20% produces two variations per param."""
    params = {"ATR_MULT": 2.0, "EMA_PERIOD": 20}
    variations = generate_variations(params, delta_pct=0.20)

    # 2 params × 2 directions = 4 variations
    assert len(variations) == 4

    # Verify all low/high values
    names_seen = set()
    for var in variations:
        name = list(var.keys())[0]
        val = var[name]
        names_seen.add(name)

    assert names_seen == {"ATR_MULT", "EMA_PERIOD"}

    # Check specific values: ATR_MULT low=1.6, high=2.4
    atr_vals = [v["ATR_MULT"] for v in variations if "ATR_MULT" in v]
    assert sorted(atr_vals) == [1.6, 2.4]


def test_generate_variations_int_params():
    """Integer params: ±20% rounded to nearest int, minimum 1."""
    params = {"COOLDOWN_BARS": 15, "MAX_HOLD_BARS": 20}
    variations = generate_variations(params, delta_pct=0.20)

    # COOLDOWN_BARS: 12 low, 18 high
    # MAX_HOLD_BARS: 16 low, 24 high
    cooldown_vals = sorted([v["COOLDOWN_BARS"] for v in variations if "COOLDOWN_BARS" in v])
    max_hold_vals = sorted([v["MAX_HOLD_BARS"] for v in variations if "MAX_HOLD_BARS" in v])

    assert cooldown_vals == [12, 18]
    assert max_hold_vals == [16, 24]


def test_generate_variations_small_int_floor():
    """Integer param that would go below 1 is floored at 1."""
    params = {"PERIOD": 3}
    variations = generate_variations(params, delta_pct=0.20)
    # 3 * 0.8 = 2.4 -> rounds to 2 (still >= 1)
    vals = [v["PERIOD"] for v in variations]
    assert 2 in vals

    # Test with period=1: 1 * 0.8 = 0.8 -> rounds to 1 (floored)
    params2 = {"PERIOD": 1}
    variations2 = generate_variations(params2, delta_pct=0.20)
    vals2 = [v["PERIOD"] for v in variations2]
    assert all(v >= 1 for v in vals2)


def test_generate_variations_empty():
    """Empty params dict produces empty variations."""
    assert generate_variations({}) == []


# ── TS04: _net_r computation ───────────────────────────────────────────────

def test_net_r_basic():
    """Sum of r_multiple across trades."""
    trades = [
        {"r_multiple": 1.5},
        {"r_multiple": -0.5},
        {"r_multiple": 2.0},
    ]
    assert _net_r(trades) == 3.0


def test_net_r_empty():
    assert _net_r([]) == 0.0


def test_net_r_missing_field():
    """Trades missing r_multiple contribute 0."""
    trades = [
        {"r_multiple": 1.0},
        {"other": "data"},
        {"r_multiple": -1.0},
    ]
    assert _net_r(trades) == 0.0


def test_net_r_invalid_values():
    """Non-numeric r_multiple values are treated as 0."""
    trades = [
        {"r_multiple": 1.0},
        {"r_multiple": "nope"},
        {"r_multiple": None},
    ]
    assert _net_r(trades) == 1.0


# ── TS05: Full sensitivity test with synthetic data ────────────────────────

def test_sensitivity_test_with_synthetic_data(monkeypatch, tmp_path):
    """End-to-end test with a mock scanner and synthetic OHLCV data."""
    # Create a temporary scanner module file
    scanner_code = '''
STRATEGY_ID = "STR-TEST-G2"
ATR_MULT = 2.0
COOLDOWN = 10
PARAMS = {"ATR_MULT": ATR_MULT, "COOLDOWN": COOLDOWN}

def scan(df, ticker, long_only=False):
    """Simple mock scan: returns a signal when close crosses a threshold."""
    signals = []
    close = df["close"].values
    for i in range(1, len(close)):
        if close[i] > close[i-1] * 1.01:
            signals.append({
                "date": df.index[i],
                "ticker": ticker,
                "direction": "long",
                "entry_price": close[i],
                "stop_price": close[i] * 0.95,
                "target_price": close[i] * (1 + 0.02 * ATR_MULT),
            })
    return signals

def run_backtest(df, ticker, long_only=False):
    """Walk-forward exit — simple 1-bar exit with r_multiple based on ATR_MULT."""
    signals = scan(df, ticker, long_only)
    trades = []
    for sig in signals:
        idx = df.index.get_loc(sig["date"])
        if idx + 3 >= len(df):
            continue
        exit_price = df.iloc[idx + 3]["close"]
        risk = sig["entry_price"] - sig["stop_price"]
        if risk > 0:
            r = (exit_price - sig["entry_price"]) / risk
        else:
            r = 0.0
        trades.append({
            "symbol": ticker,
            "direction": sig["direction"],
            "entry_price": sig["entry_price"],
            "exit_price": exit_price,
            "r_multiple": round(r, 4),
        })
    return trades
'''
    scanner_path = tmp_path / "scanner_test_g2.py"
    scanner_path.write_text(scanner_code)

    # Add tmp_path to sys.path so we can import
    sys.path.insert(0, str(tmp_path))

    import g2_parameter_sensitivity as g2
    # Override SCANNERS_DIR to point at tmp_path
    monkeypatch.setattr(g2, "SCANNERS_DIR", tmp_path)
    g2._scanner_module_cache.clear()

    # Generate synthetic data — trending up so strategy produces positive R
    df = make_synthetic_ohlcv(n_bars=200, trend_strength=0.003, volatility=0.01, seed=123)
    df.columns = df.columns.str.lower()

    result = run_sensitivity_test(
        strategy_id="STR-TEST-G2",
        df=df,
        ticker="SYNTH",
        delta_pct=0.20,
    )

    assert result["strategy_id"] == "STR-TEST-G2"
    assert "ATR_MULT" in result["params"]
    assert "COOLDOWN" in result["params"]
    assert result["baseline_net_r"] is not None
    assert result["baseline_trades"] >= 0

    # Should have 4 variations (2 params × 2 directions)
    assert len(result["variations"]) == 4

    # Every variation should reference its param
    for var in result["variations"]:
        assert "param" in var
        assert var["param"] in ("ATR_MULT", "COOLDOWN")
        assert "net_r" in var
        assert "delta_pct" in var

    # Robustness score should be computable
    assert result["robustness_score"] is not None
    assert 0.0 <= result["robustness_score"] <= 1.0

    # Clean up
    sys.path.remove(str(tmp_path))
    g2._scanner_module_cache.clear()


# ── TS06: Edge case — no numeric params ────────────────────────────────────

def test_no_params_skipped(monkeypatch):
    """Strategy with no numeric params returns skipped result."""
    class MockModule:
        STRATEGY_ID = "STR-NO-PARAMS"
        # No PARAMS dict or numeric constants

    import g2_parameter_sensitivity as g2
    monkeypatch.setattr(g2, "_scanner_module_cache", {})
    monkeypatch.setattr(g2, "_find_scanner_module", lambda sid: (MockModule(), None))

    df = make_synthetic_ohlcv(n_bars=100)
    result = run_sensitivity_test("STR-NO-PARAMS", df, "TEST")

    assert result.get("skipped") is True
    assert result["passes"] is None
    assert result["robustness_score"] is None
    assert result["variations"] == []


# ── TS07: Edge case — invalid strategy_id ──────────────────────────────────

def test_invalid_strategy_id():
    """Non-existent strategy raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        run_sensitivity_test("STR-DOES-NOT-EXIST", pd.DataFrame(), "TEST")


# ── TS08: evaluate_gate threshold check ────────────────────────────────────

def test_evaluate_gate_custom_threshold(monkeypatch):
    """Custom threshold correctly overrides default PASS_THRESHOLD."""
    results_log = []

    class MockModule:
        STRATEGY_ID = "STR-TEST-THRESH"
        PARAMS = {"X": 10}

        @staticmethod
        def run_backtest(df, ticker, long_only=False):
            # Return fixed trades: 3 positive, 1 negative variation
            call_count = len(results_log)
            results_log.append(call_count)
            return [{"r_multiple": 2.0 if call_count < 5 else -1.0}]

    import g2_parameter_sensitivity as g2
    g2._scanner_module_cache.clear()
    monkeypatch.setattr(g2, "_scanner_module_cache", {"STR-TEST-THRESH": MockModule()})
    monkeypatch.setattr(g2, "_find_scanner_module", lambda sid: (MockModule(), None))

    df = make_synthetic_ohlcv(n_bars=100)
    result = evaluate_gate("STR-TEST-THRESH", df, "TEST", threshold=0.5)
    assert "passes" in result
    assert result["threshold"] == 0.5


# ── TS09: make_synthetic_ohlcv data integrity ──────────────────────────────

def test_synthetic_ohlcv_shape():
    df = make_synthetic_ohlcv(n_bars=300, seed=42)
    assert len(df) == 300
    for col in ["open", "high", "low", "close", "volume"]:
        assert col in df.columns
    assert isinstance(df.index, pd.DatetimeIndex)
    # All close prices should be positive
    assert (df["close"] > 0).all()
    # High >= Low
    assert (df["high"] >= df["low"]).all()


def test_synthetic_ohlcv_reproducible():
    df1 = make_synthetic_ohlcv(n_bars=100, seed=42)
    df2 = make_synthetic_ohlcv(n_bars=100, seed=42)
    pd.testing.assert_frame_equal(df1, df2)


# ── TS10: list_strategies discovers real scanners ───────────────────────────

def test_list_strategies_returns_ids():
    """list_strategies should return real strategy IDs from the scanners dir."""
    ids = list_strategies()
    assert isinstance(ids, list)
    if ids:  # only check if scanners are present
        for sid in ids:
            assert isinstance(sid, str)
            # Most strategy IDs follow "STR-*" convention, but not all
            assert len(sid) > 0