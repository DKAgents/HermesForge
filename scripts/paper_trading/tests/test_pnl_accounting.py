"""
Tests for pnl_accounting.py — the shared PnL-accounting module.

US-167: _adversarial_cost_drag self-guard (non-positive prices -> +inf,
no exception). US-166: _apply_taker_fee direction threading.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math

from pnl_accounting import (
    _adversarial_cost_drag,
    _apply_taker_fee,
    _paper_r,
    _compute_r,
)


# ---------------------------------------------------------------------------
# US-167: self-guard in _adversarial_cost_drag
# ---------------------------------------------------------------------------

def test_cost_drag_zero_entry_returns_inf():
    assert _adversarial_cost_drag(0.0, 100.0) == float("inf")


def test_cost_drag_negative_entry_returns_inf():
    assert _adversarial_cost_drag(-1.0, 100.0) == float("inf")


def test_cost_drag_zero_stop_returns_inf():
    assert _adversarial_cost_drag(100.0, 0.0) == float("inf")


def test_cost_drag_negative_stop_returns_inf():
    assert _adversarial_cost_drag(100.0, -1.0) == float("inf")


def test_cost_drag_both_nonpositive_returns_inf():
    assert _adversarial_cost_drag(0.0, 0.0) == float("inf")
    assert _adversarial_cost_drag(-1.0, -1.0) == float("inf")


def test_cost_drag_normal_path_unchanged():
    # risk_pct = 1% -> 20 bps / 10000 / 0.01 = 0.2
    assert abs(_adversarial_cost_drag(100.0, 99.0) - 0.2) < 1e-12


def test_cost_drag_degenerate_still_inf():
    # risk_pct < DEGENERATE_RISK_FLOOR (0.001) -> inf
    assert _adversarial_cost_drag(100.0, 99.999) == float("inf")


# ---------------------------------------------------------------------------
# US-166: taker-fee direction
# ---------------------------------------------------------------------------

def test_buy_leg_is_adverse():
    # long entry and short exit-cover are BUY legs: cost more than raw price
    assert _apply_taker_fee(100.0, "long", True, 10.0) > 100.0
    assert _apply_taker_fee(100.0, "short", False, 10.0) > 100.0
    assert abs(_apply_taker_fee(100.0, "long", True, 10.0) - 100.1) < 1e-9


def test_sell_leg_is_adverse():
    # long exit and short entry are SELL legs: net LESS than raw price
    assert _apply_taker_fee(100.0, "long", False, 10.0) < 100.0
    assert _apply_taker_fee(100.0, "short", True, 10.0) < 100.0
    assert abs(_apply_taker_fee(100.0, "short", True, 10.0) - 99.9) < 1e-9


def test_long_round_trip_pays_full_adverse_fee():
    taker = 10.0
    entry = _apply_taker_fee(100.0, "long", True, taker)   # buy: 100.1
    exitp = _apply_taker_fee(105.0, "long", False, taker)  # sell: 105 * 0.999
    assert abs(entry - 100.0 * (1 + taker / 10000)) < 1e-9
    assert abs(exitp - 105.0 * (1 - taker / 10000)) < 1e-9


def test_short_round_trip_pays_full_adverse_fee():
    taker = 10.0
    entry = _apply_taker_fee(100.0, "short", True, taker)  # sell: 100 * 0.999
    exitp = _apply_taker_fee(95.0, "short", False, taker)  # buy: 95 * 1.001
    assert abs(entry - 100.0 * (1 - taker / 10000)) < 1e-9
    assert abs(exitp - 95.0 * (1 + taker / 10000)) < 1e-9


def test_long_and_short_round_trips_charge_equal_total_fee():
    """A long round trip and a short round trip each pay exactly 2 * taker_bps
    in adverse fees — the old direction-blind (favorable sell-leg) path is gone."""
    taker = 10.0

    # Flat round trip (buy then sell the same price): gross 0, fee = 2 * 10 bps.
    l_entry = _apply_taker_fee(100.0, "long", True, taker)   # buy: 100.1
    l_exit = _apply_taker_fee(100.0, "long", False, taker)   # sell: 99.9
    long_fee = l_entry - l_exit                              # 0.2 == 20 bps

    s_entry = _apply_taker_fee(100.0, "short", True, taker)  # sell: 99.9
    s_exit = _apply_taker_fee(100.0, "short", False, taker)  # buy: 100.1
    short_fee = s_exit - s_entry                             # 0.2 == 20 bps

    assert abs(long_fee - 0.2) < 1e-9
    assert abs(short_fee - 0.2) < 1e-9
    # Both directions pay the SAME total adverse fee.
    assert abs(long_fee - short_fee) < 1e-12


if __name__ == "__main__":
    import inspect
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all pnl_accounting tests passed")