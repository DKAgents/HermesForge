"""
Tests for the live-trading safety fixes (Phase 0 audit).

Covers:
  - P0-1: kill switch must block OPENING but never CLOSING positions.
  - P0-2: open_position must place a protective stop-loss order.
  - P1-4: open_position must independently enforce the $500 hard size cap.
"""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

import live_executor as le
import live_risk_manager as lrm


# ── Helpers ─────────────────────────────────────────────────────────────────

def make_executor():
    """Build a LiveExecutor with mocked exchange/info (no network, no creds)."""
    ex = le.LiveExecutor()
    ex._exchange = MagicMock()
    ex._info = MagicMock()
    ex._address = "0xTEST"
    ex._info.all_mids = MagicMock(return_value={"ETH": 3000.0, "BTC": 60000.0})
    ex._exchange.market_open = MagicMock(return_value={"status": "ok"})
    ex._exchange.market_close = MagicMock(return_value={"status": "ok"})
    ex._exchange.order = MagicMock(return_value={"status": "ok"})
    return ex


def arm_kill_switch(monkeypatch, tmp_path):
    """Arm the kill switch by pointing KILL_SWITCH_FILE at a tmp file (PAUSED=true)."""
    kf = tmp_path / "live_kill_switch"
    kf.write_text("PAUSED=true")
    monkeypatch.setattr(le, "KILL_SWITCH_FILE", kf)
    return kf


# ═════════════════════════════════════════════════════════════════════════════
# P0-1: kill switch must NOT block closing positions
# ═════════════════════════════════════════════════════════════════════════════

def test_close_position_allowed_when_kill_switch_armed(tmp_path, monkeypatch):
    arm_kill_switch(monkeypatch, tmp_path)

    ex = make_executor()
    ex.get_positions = MagicMock(return_value=[
        {"coin": "ETH", "size": 1.0, "entry_px": 2900.0, "unrealized_pnl": 100.0}
    ])

    result = ex.close_position("ETH")

    assert result.success, f"close must succeed despite kill switch: {result.error}"
    assert ex._exchange.market_close.called, "flatten must be attempted"


def test_open_position_blocked_when_kill_switch_armed(tmp_path, monkeypatch):
    arm_kill_switch(monkeypatch, tmp_path)

    ex = make_executor()

    result = ex.open_position("ETH", "long", 500.0, stop_loss_pct=0.02)

    assert not result.success, "open must be blocked by kill switch"
    assert not ex._exchange.market_open.called


# ═════════════════════════════════════════════════════════════════════════════
# P0-2: open_position must place a protective stop-loss order
# ═════════════════════════════════════════════════════════════════════════════

def test_open_position_places_stop_loss():
    ex = make_executor()

    result = ex.open_position("ETH", "long", 500.0, stop_loss_pct=0.02)

    assert result.success
    assert ex._exchange.market_open.called
    assert ex._exchange.order.called, "a stop-loss (trigger) order must be placed"

    # The stop order should be a reduce-only SELL with a stop trigger below mid.
    call_kwargs = ex._exchange.order.call_args.kwargs
    assert call_kwargs.get("is_buy") is False, "long stop = sell reduce-only"
    assert call_kwargs.get("reduce_only") is True, "stop must never open a position"


def test_flatten_when_stop_loss_placement_fails():
    """Fail-closed: if the stop can't be placed, the position is flattened immediately."""
    ex = make_executor()
    ex._exchange.order = MagicMock(side_effect=Exception("stop placement failed"))
    ex._exchange.market_close = MagicMock(return_value={"status": "ok"})

    result = ex.open_position("ETH", "long", 500.0, stop_loss_pct=0.02)

    assert not result.success, "must fail-closed when the stop cannot be placed"
    assert ex._exchange.market_close.called, "must flatten the position when the stop fails"


# ═════════════════════════════════════════════════════════════════════════════
# P1-4: open_position must independently enforce the hard size cap
# ═════════════════════════════════════════════════════════════════════════════

def test_open_position_rejects_oversized_without_caller_check():
    ex = make_executor()

    # Call directly with an oversized notional, bypassing the risk manager.
    result = ex.open_position("ETH", "long", 600.0, stop_loss_pct=0.02)

    assert not result.success, "executor must reject size > $500 on its own"
    assert not ex._exchange.market_open.called


def test_open_position_allows_size_within_cap():
    ex = make_executor()

    result = ex.open_position("ETH", "long", 500.0, stop_loss_pct=0.02)

    assert result.success
    assert ex._exchange.market_open.called


# ═════════════════════════════════════════════════════════════════════════════
# Risk manager: existing logic is solid — pin it with regression tests too
# ═════════════════════════════════════════════════════════════════════════════

def test_risk_manager_enforces_max_size():
    rm = lrm.LiveRiskManager()
    # force clean daily state
    rm._state = {"daily_loss": 0.0, "daily_stops": 0, "date": "2000-01-01",
                 "consecutive_stops": 0, "circuit_breaker_until": ""}

    check = rm.check_trade(size_usd=600.0, open_positions=[], current_exposure_usd=0.0)
    assert not check.allowed
    assert "exceed" in check.reason.lower() or "max" in check.reason.lower()