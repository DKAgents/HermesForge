"""
Tests for decay_watch.py — D1 through D7.
"""

import sys
import os
import tempfile
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import decay_watch as dw


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_trade(pnl=100.0, R=1.5, realised_slippage=0.001, modelled_slippage=0.001):
    return {
        "pnl": pnl,
        "R": R,
        "realised_slippage": realised_slippage,
        "modelled_slippage": modelled_slippage,
    }


def _make_trades(n, pnl=100.0, R=1.5):
    return [_make_trade(pnl=pnl, R=R) for _ in range(n)]


# =============================================================================
# D1: healthy strategy stays active
# =============================================================================

def test_D1_healthy_strategy_stays_active():
    trades = _make_trades(120, pnl=100.0, R=2.0)
    result = dw.check_decay("S1", trades)
    assert result["healthy"] is True
    assert result["trigger"] is None
    pf = result["metrics"]["trailing_pf"]
    if pf == "inf":
        pass  # all winners — definitely healthy
    else:
        assert float(pf) > 1.15


# =============================================================================
# D2: trailing PF < 1.15 → triggers decay
# =============================================================================

def test_D2_trailing_pf_below_threshold():
    # Create 100 trades with PF barely above 1.0
    trades = []
    for i in range(50):
        trades.append(_make_trade(pnl=100.0, R=1.0))   # wins
    for i in range(50):
        trades.append(_make_trade(pnl=-95.0, R=-1.0))  # losses
    # PF = 5000 / 4750 = 1.0526 < 1.15

    result = dw.check_decay("S1", trades)
    assert result["healthy"] is False
    assert "PF" in result["trigger"]


# =============================================================================
# D3: trailing avg R < 0 for 2 windows → triggers decay
# =============================================================================

def test_D3_avg_R_negative_two_windows():
    # Need at least 40 trades for 2 non-overlapping windows of 20
    trades = []
    # Window 1 (oldest 20): negative avg R
    for _ in range(20):
        trades.append(_make_trade(pnl=-50.0, R=-1.0))
    # Window 2 (next 20): negative avg R
    for _ in range(20):
        trades.append(_make_trade(pnl=-30.0, R=-0.5))

    result = dw.check_decay("S1", trades, pf_window=200, avg_r_window=20, avg_r_consecutive=2)
    assert result["healthy"] is False
    assert "avg R" in result["trigger"]


# =============================================================================
# D4: slippage > 2x for 20 trades → triggers decay
# =============================================================================

def test_D4_slippage_exceeds_2x_20_trades():
    trades = []
    for _ in range(20):
        trades.append(_make_trade(
            pnl=50.0,
            R=1.0,
            realised_slippage=0.003,
            modelled_slippage=0.001,  # realised is 3x modelled
        ))

    result = dw.check_decay("S1", trades, pf_window=200, slippage_window=20, slippage_ratio=2.0)
    assert result["healthy"] is False
    assert "slippage" in result["trigger"]


# =============================================================================
# D5: single bad window doesn't trigger (needs 2 consecutive)
# =============================================================================

def test_D5_single_bad_window_no_trigger():
    trades = []
    # One bad window
    for _ in range(20):
        trades.append(_make_trade(pnl=-50.0, R=-1.0))
    # One good window (not enough to reset the streak? Actually it does reset
    # because the check looks for consecutive negative windows)
    for _ in range(20):
        trades.append(_make_trade(pnl=100.0, R=2.0))

    # Windows from newest: good (R>0), then bad (R<0) — only one consecutive bad
    result = dw.check_decay("S1", trades, pf_window=200, avg_r_window=20, avg_r_consecutive=2)
    assert result["healthy"] is True
    assert result["trigger"] is None


# =============================================================================
# D6: auto_demote moves note and creates review
# =============================================================================

def test_D6_auto_demote_creates_review():
    result = dw.auto_demote("S1", "trailing-100-trade PF 1.05 < 1.15")
    assert result["strategy_id"] == "S1"
    assert result["action"] == "auto_demote"
    assert result["from_status"] == "Active"
    assert result["to_status"] == "Hypotheses"
    assert result["review_required"] is True
    assert "review_note" in result
    assert "S1" in result["review_note"]


# =============================================================================
# D7: empty trade list → healthy
# =============================================================================

def test_D7_empty_trade_list_healthy():
    result = dw.check_decay("S1", [])
    assert result["healthy"] is True
    assert result["trigger"] is None
    assert result["metrics"]["trailing_pf"] is None


# ═══════════════════════════════════════════════════════════════════════════════
# watch_all integration tests
# ═══════════════════════════════════════════════════════════════════════════════

def test_watch_all_csv_parsing():
    """watch_all reads a CSV and processes active strategies."""
    csv_content = (
        "strategy_id,ticker,pnl,R,realised_slippage,modelled_slippage,timestamp\n"
    )
    # Add 120 winning trades for S1
    for i in range(120):
        csv_content += f"S1,BTC-USD,100.0,2.0,0.001,0.001,2024-01-{i % 28 + 1:02d}\n"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        tmpfile = f.name

    try:
        result = dw.watch_all(tmpfile, ["S1", "S2"])
        assert len(result["actions"]) == 0
        assert "0 strategy" in result["summary"]
    finally:
        os.unlink(tmpfile)


def test_watch_all_detects_decay():
    """watch_all flags a strategy with bad PF."""
    csv_content = (
        "strategy_id,ticker,pnl,R,realised_slippage,modelled_slippage,timestamp\n"
    )
    # 50 wins + 50 losses → PF ~1.05
    for i in range(50):
        csv_content += f"S1,BTC-USD,100.0,1.0,0.001,0.001,2024-01-{i % 28 + 1:02d}\n"
    for i in range(50):
        csv_content += f"S1,BTC-USD,-95.0,-1.0,0.001,0.001,2024-02-{i % 28 + 1:02d}\n"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        tmpfile = f.name

    try:
        result = dw.watch_all(tmpfile, ["S1"])
        assert len(result["actions"]) == 1
        assert result["actions"][0]["action"] == "auto_demote"
    finally:
        os.unlink(tmpfile)


def test_watch_all_missing_file():
    result = dw.watch_all("/nonexistent/path.csv", ["S1"])
    assert result["actions"] == []