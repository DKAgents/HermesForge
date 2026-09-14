"""Tests for g0_cost_screen.py — G01 through G05."""
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
import pandas as pd

from g0_cost_screen import (
    screen,
    screen_from_parquet,
    batch_screen,
    summary_report,
    TAKER_FEE_BPS,
    DEFAULT_SLIPPAGE_BPS,
    FUNDING_OVERHEAD_BPS,
    GROSS_MULTIPLIER,
    compute_median_abs_move,
)


# ---------------------------------------------------------------------------
# G01: screen on a volatile symbol passes
# ---------------------------------------------------------------------------
def test_volatile_symbol_passes():
    # Volatile: ~10% moves each bar, median ~1000 bps
    np.random.seed(42)
    prices = 100 * (1 + np.cumsum(np.random.normal(0, 0.05, 500)))
    prices = np.abs(prices) + 50  # ensure positive

    result = screen("VOL", prices)
    assert result["passes"] is True
    assert result["median_abs_move_bps"] > 50  # well above cost
    all_in = TAKER_FEE_BPS + DEFAULT_SLIPPAGE_BPS + FUNDING_OVERHEAD_BPS
    assert result["all_in_cost_bps"] == all_in
    assert result["gross_capture_needed_bps"] == all_in * GROSS_MULTIPLIER


# ---------------------------------------------------------------------------
# G02: screen on a flat symbol fails with explanation
# ---------------------------------------------------------------------------
def test_flat_symbol_fails():
    # Very flat: ~0.01% moves
    np.random.seed(123)
    prices = 100 + np.cumsum(np.random.normal(0, 0.005, 500))
    prices = np.abs(prices) + 50

    result = screen("FLAT", prices)
    assert result["passes"] is False
    assert "median" in result["explanation"].lower()
    assert "gross capture needed" in result["explanation"].lower()
    assert str(TAKER_FEE_BPS) in result["explanation"] or "fee" in result["explanation"].lower()


# ---------------------------------------------------------------------------
# G03: batch_screen returns sorted results
# ---------------------------------------------------------------------------
def test_batch_screen_sorted():
    tmpdir = tempfile.mkdtemp()

    try:
        # Create a volatile symbol
        np.random.seed(1)
        prices_vol = 100 * (1 + np.cumsum(np.random.normal(0, 0.03, 200)))
        prices_vol = np.abs(prices_vol) + 50
        df_vol = pd.DataFrame({"close": prices_vol, "open": prices_vol, "high": prices_vol, "low": prices_vol, "volume": 1.0})
        df_vol.to_parquet(os.path.join(tmpdir, "VOLATILE.parquet"))

        # Create a flat symbol
        prices_flat = 100 + np.cumsum(np.random.normal(0, 0.001, 200))
        prices_flat = np.abs(prices_flat) + 50
        df_flat = pd.DataFrame({"close": prices_flat, "open": prices_flat, "high": prices_flat, "low": prices_flat, "volume": 1.0})
        df_flat.to_parquet(os.path.join(tmpdir, "FLAT.parquet"))

        results = batch_screen(tmpdir)

        assert len(results) >= 2
        # Results should be sorted descending by median_abs_move_bps
        moves = [r["median_abs_move_bps"] for r in results if "error" not in r]
        assert moves == sorted(moves, reverse=True), f"Not sorted: {moves}"

        # Volatile should be first
        assert results[0]["symbol"] in ("VOLATILE", "VOL")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# G04: all_in_cost includes fees + slippage + funding
# ---------------------------------------------------------------------------
def test_all_in_cost_components():
    prices = np.array([100, 101, 102, 103, 104, 105])  # 1% moves

    # Test with custom slippage and funding
    result = screen("TEST", prices, slippage_bps=5.0, funding_bps=3.0)

    expected_all_in = TAKER_FEE_BPS + 5.0 + 3.0
    assert result["all_in_cost_bps"] == expected_all_in
    assert result["fee_bps"] == TAKER_FEE_BPS
    assert result["slippage_bps"] == 5.0
    assert result["funding_bps"] == 3.0

    # Test with defaults
    result_default = screen("TEST", prices)
    assert result_default["all_in_cost_bps"] == TAKER_FEE_BPS + DEFAULT_SLIPPAGE_BPS + FUNDING_OVERHEAD_BPS


# ---------------------------------------------------------------------------
# G05: 4x multiplier applied correctly
# ---------------------------------------------------------------------------
def test_multiplier_applied():
    prices = np.array([100, 101, 100.5, 101.5, 100, 101])
    result = screen("TEST", prices)
    all_in = result["all_in_cost_bps"]
    assert result["gross_capture_needed_bps"] == all_in * GROSS_MULTIPLIER
    assert result["multiplier"] == GROSS_MULTIPLIER

    # Test with custom multiplier
    result_custom = screen("TEST", prices, gross_multiplier=6.0)
    assert result_custom["gross_capture_needed_bps"] == all_in * 6.0
    assert result_custom["multiplier"] == 6.0


# ---------------------------------------------------------------------------
# Additional edge case: compute_median_abs_move on DataFrame
# ---------------------------------------------------------------------------
def test_compute_median_abs_move():
    df = pd.DataFrame({"close": [100.0, 101.0, 102.0, 103.0, 104.0]})
    # moves: |1/100|=0.01, |1/101|≈0.0099, |1/102|≈0.0098, |1/103|≈0.00971
    # in bps: ~100, ~99, ~98, ~97 → median ≈ 98.5 bps
    med = compute_median_abs_move(df)
    assert med > 90
    assert med < 110


def test_screen_from_parquet():
    tmpdir = tempfile.mkdtemp()
    try:
        df = pd.DataFrame({
            "close": [100.0, 101.0, 100.5, 101.5, 100.0],
            "symbol": ["TESTCOIN"] * 5,
        })
        path = os.path.join(tmpdir, "TESTCOIN.parquet")
        df.to_parquet(path)

        result = screen_from_parquet(path)
        assert result["symbol"] == "TESTCOIN"
        assert "median_abs_move_bps" in result
        assert "passes" in result
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_insufficient_data():
    result = screen("TINY", [100.0])
    assert result["passes"] is False
    assert "insufficient" in result["explanation"].lower()


def test_summary_report():
    results = [
        {"symbol": "A", "passes": True, "median_abs_move_bps": 100.0},
        {"symbol": "B", "passes": False, "median_abs_move_bps": 5.0},
        {"symbol": "C", "passes": True, "median_abs_move_bps": 80.0},
        {"symbol": "D", "error": "bad file"},
    ]
    rep = summary_report(results)
    assert rep["total_files"] == 4
    assert rep["valid"] == 3
    assert rep["pass"] == 2
    assert rep["fail"] == 1
    assert rep["errors"] == 1
    assert rep["pass_rate"] == 2 / 3
    assert "A" in rep["passing_symbols"]
    assert "B" in rep["failing_symbols"]