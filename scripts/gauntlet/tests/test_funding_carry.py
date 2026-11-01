"""
Tests for funding_carry.py — the US-179 funding/basis carry strategy.

Golden-vector tests for unit normalization, cost gate, position sizing, the
sustained-funding signal (incl. the single-spike rejection), and the kill rules.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd

import funding_carry as fc


def _series(rates, premiums=None):
    n = len(rates)
    premium = premiums if premiums is not None else [0.0] * n
    return pd.DataFrame({"time": range(n), "funding_rate": rates, "premium": premium})


def test_hourly_to_apr_and_back():
    assert abs(fc.hourly_to_apr(1e-6) - 0.00876) < 1e-12
    assert abs(fc.apr_to_hourly(0.08) - 9.1324200913242e-6) < 1e-12
    # round-trip
    assert abs(fc.hourly_to_apr(fc.apr_to_hourly(0.18)) - 0.18) < 1e-12


def test_cost_clears_break_even():
    # taker 24bps over 1wk break-even = 12.5%/yr (just above 0.125).
    assert fc.cost_clears(0.125, 24.0) is False
    assert fc.cost_clears(0.13, 24.0) is True
    # maker 12bps over 1wk: 6.3%/yr clears, 6.0% does not.
    assert fc.cost_clears(0.063, 12.0) is True
    assert fc.cost_clears(0.060, 12.0) is False


def test_size_position_rails():
    sz = fc.size_position(1_000_000.0, 50.0, float("inf"), True)
    # notional capped by 20% gross rail (200k), basis risk <= 1% capital.
    assert sz["notional"] == 200_000.0
    assert abs(sz["basis_risk_usd"] - 1000.0) < 1e-6
    assert sz["size_capped"] is True
    # ineligible -> zero.
    inel = fc.size_position(1_000_000.0, 50.0, float("inf"), False)
    assert inel["notional"] == 0.0 and "ineligible" in inel["cap_reason"]


def test_funding_window_signal_sustained():
    # 24 hours at a steady positive rate -> 13%/yr clears the S4 taker gate
    # (break-even = 12.5%/yr), all 24h positive (S2), current > 0 (S3).
    hourly = fc.apr_to_hourly(0.13)
    sig = fc.funding_window_signal(_series([hourly] * 24))
    assert sig["sustained"] is True
    assert sig["positive_fraction"] == 1.0
    assert abs(sig["mean_apr"] - 0.13) < 1e-6


def test_funding_window_signal_single_spike_rejected():
    # one 0.5%/hr spike + 23 ~0 hours -> S2 positive fraction 1/24 < 0.75 rejects.
    rates = [0.0] * 23 + [0.005]
    sig = fc.funding_window_signal(_series(rates))
    assert sig["sustained"] is False
    assert sig["positive_fraction"] < fc.FUNDING_POSITIVE_FRACTION
    assert any("S2" in r for r in sig["reasons"])


def test_funding_window_signal_requires_cost_clear():
    # 9%/yr (>= 8% S1) but below the taker break-even -> S4 fails.
    hourly = fc.apr_to_hourly(0.09)
    sig = fc.funding_window_signal(_series([hourly] * 24))
    assert sig["sustained"] is False
    assert any("S4" in r for r in sig["reasons"])


def test_kill_rules():
    assert fc.rate_flip(_series([1e-5, -1e-6])) is True
    assert fc.rate_flip(_series([1e-5, 1e-6])) is False
    # basis_widen bps
    assert abs(fc.basis_widen(1.005, 1.0) - 50.0) < 1e-6
    # decay: 3%/yr rolling mean below 4% -> True
    hourly = fc.apr_to_hourly(0.03)
    assert fc.funding_decaying(_series([hourly] * 24)) is True
    hourly2 = fc.apr_to_hourly(0.10)
    assert fc.funding_decaying(_series([hourly2] * 24)) is False


def test_carry_g3_record_empty():
    rec = fc.carry_g3_record(pd.DataFrame())
    assert rec["n"] == 0 and rec["passed"] is False


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all funding_carry tests passed")