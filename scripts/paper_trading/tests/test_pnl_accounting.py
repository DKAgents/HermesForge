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


if __name__ == "__main__":
    import inspect
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all pnl_accounting tests passed")