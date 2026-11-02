"""
Tests for funding_carry.py — the US-185 funding-carry reconstitution.

Golden-vector tests for unit normalization, cost gate, the sustained-funding
signal (positive AND negative directions), position sizing (1R = 1% capital,
the §3.2/§3.3 invariant), the directional risk model (λ hurdle + hard stop),
execution-form dispatch, spot-leg resolution, and the real-basis kill-stop.
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd

import funding_carry as fc


def _series(rates, premiums=None):
    n = len(rates)
    premium = premiums if premiums is not None else [0.0] * n
    return pd.DataFrame({"time": range(n), "funding_rate": rates, "premium": premium})


# ── unit normalization ───────────────────────────────────────────────────────
def test_hourly_to_apr_and_back():
    assert abs(fc.hourly_to_apr(1e-6) - 0.00876) < 1e-12
    assert abs(fc.apr_to_hourly(0.08) - 9.1324200913242e-6) < 1e-12
    assert abs(fc.hourly_to_apr(fc.apr_to_hourly(0.18)) - 0.18) < 1e-12


def test_cost_clears_break_even():
    assert fc.cost_clears(0.125, 24.0) is False
    assert fc.cost_clears(0.13, 24.0) is True
    assert fc.cost_clears(0.063, 12.0) is True
    assert fc.cost_clears(0.060, 12.0) is False


# ── sizing: 1R = 1% capital (the §3.2 / §3.3 invariant) ──────────────────────
def test_size_directional_risk_budget_binds():
    # 1% capital / 2% stop = 0.5× capital notional; risk_usd == exactly 1% capital.
    sz = fc.size_position(1_000_000.0, fc.DIRECTIONAL_STOP_BPS, float("inf"),
                          "directional_short")
    assert abs(sz["notional"] - 500_000.0) < 1e-6
    assert abs(sz["risk_usd"] - 10_000.0) < 1e-6   # 1% of $1M
    assert sz["size_capped"] is False               # the risk budget binds (honest 1R)


def test_size_delta_neutral_cap_does_not_silently_shrink_r():
    # 50bp stop rail wants $2M but the 1× gross cap (gated, no leverage) binds at
    # $1M -> risk_usd MUST be re-derived to $5k (0.5%), size_capped=True.
    sz = fc.size_position(1_000_000.0, fc.KILL_BASIS_BPS, float("inf"),
                          "delta_neutral")
    assert abs(sz["notional"] - 1_000_000.0) < 1e-6
    assert abs(sz["risk_usd"] - 5_000.0) < 1e-6   # re-derived from ACTUAL notional
    assert sz["size_capped"] is True
    assert sz["cap_reason"] == "gross notional cap"


def test_size_oi_capacity_binds():
    # OI capacity (2% of OI) is the tightest rail.
    oi = 4_000_000.0   # 2% = $80k < both the budget ($500k) and the 1× cap ($1M)
    sz = fc.size_position(1_000_000.0, fc.DIRECTIONAL_STOP_BPS, oi,
                          "directional_short")
    assert abs(sz["notional"] - 80_000.0) < 1e-6
    assert abs(sz["risk_usd"] - 80_000.0 * 0.02) < 1e-6   # notional * stop_frac
    assert sz["size_capped"] is True


def test_size_ineligible_zero():
    s = fc.size_position(1_000_000.0, 50.0, float("inf"), "directional_short", False)
    assert s["notional"] == 0.0 and s["risk_usd"] == 0.0 and s["size_capped"] is True


def test_gross_cap():
    assert abs(fc.gross_cap(1_000_000.0, "directional_short") - 1_000_000.0) < 1e-6
    assert abs(fc.gross_cap(1_000_000.0, "delta_neutral") - 1_000_000.0) < 1e-6


# ── directional risk model (§1.4) ────────────────────────────────────────────
def test_realized_annualized_vol_flat_series_is_zero():
    closes = pd.Series([100.0] * 100)
    assert fc.realized_annualized_vol(closes) == 0.0


def test_realized_annualized_vol_insufficient():
    assert fc.realized_annualized_vol(pd.Series([100.0])) == 0.0
    assert fc.realized_annualized_vol(pd.Series([])) == 0.0


def test_realized_annualized_vol_positive():
    # A gently trending series yields a small positive annualized vol.
    closes = pd.Series([100.0 * (1.0001 ** i) for i in range(200)])
    vol = fc.realized_annualized_vol(closes)
    assert vol > 0.0
    assert math.isfinite(vol)


def test_directional_hurdle_and_gate():
    # vol 0.5 -> hurdle = max(0.08, 0.5*0.5) = 0.25.
    assert abs(fc.directional_hurdle_apr(0.5) - 0.25) < 1e-12
    # vol 0.1 -> hurdle = max(0.08, 0.05) = 0.08 (floor).
    assert abs(fc.directional_hurdle_apr(0.1) - 0.08) < 1e-12
    assert fc.directional_risk_gate(0.30, 0.5)["eligible"] is True
    assert fc.directional_risk_gate(0.10, 0.5)["eligible"] is False
    g = fc.directional_risk_gate(0.10, 0.5)
    assert g["hurdle_apr"] == 0.25 and g["reason"]


# ── dispatch (§1.3) ──────────────────────────────────────────────────────────
def test_dispatch_execution_form():
    assert fc.dispatch_execution_form(0.01) == "directional_short"
    assert fc.dispatch_execution_form(-0.01) == "directional_long"
    assert fc.dispatch_execution_form(0.0) == "skip"
    assert fc.dispatch_execution_form(0.01, delisted=True) == "skip"
    # spot available does NOT flip to delta_neutral while gated (default off).
    assert fc.dispatch_execution_form(0.01, {"available": True}) == "directional_short"


# ── spot resolver (§1.2) ─────────────────────────────────────────────────────
def test_resolve_spot_leg_liquid_and_illiquid():
    snap = {"by_name": {
        "UBTC": {"day_ntl_vlm_usd": 1_000_000.0, "spread_bps": 5.0},
        "USOL": {"day_ntl_vlm_usd": 0.0, "spread_bps": 5.0},
    }, "available_names": ["UBTC", "USOL"]}
    # BTC -> UBTC (wrapped variant) is liquid.
    r = fc.resolve_spot_leg("BTC", snap)
    assert r["available"] is True and r["spot_name"] == "UBTC"
    # SOL -> USOL exists but zero volume -> not liquid.
    r2 = fc.resolve_spot_leg("SOL", snap)
    assert r2["available"] is False
    # XYZ -> no candidate at all.
    assert fc.resolve_spot_leg("XYZ", snap)["available"] is False


def test_resolve_spot_leg_no_snapshot():
    r = fc.resolve_spot_leg("BTC", None)
    assert r["available"] is False and "no spot snapshot" in r["reason"]


# ── funding signal (both directions) ─────────────────────────────────────────
def test_funding_window_signal_sustained():
    hourly = fc.apr_to_hourly(0.13)
    sig = fc.funding_window_signal(_series([hourly] * 24))
    assert sig["sustained"] is True
    assert sig["positive_fraction"] == 1.0
    assert abs(sig["mean_apr"] - 0.13) < 1e-6


def test_funding_window_signal_negative_sustained():
    # Sustained NEGATIVE funding -> long-perp receives funding.
    hourly = fc.apr_to_hourly(0.13)
    sig = fc.funding_window_signal(_series([-hourly] * 24), sign=-1)
    assert sig["sustained"] is True
    assert sig["positive_fraction"] == 1.0
    assert abs(sig["mean_mag_apr"] - 0.13) < 1e-6
    assert sig["mean_apr"] < 0


def test_funding_window_signal_single_spike_rejected():
    rates = [0.0] * 23 + [0.005]
    sig = fc.funding_window_signal(_series(rates))
    assert sig["sustained"] is False
    assert sig["positive_fraction"] < fc.FUNDING_POSITIVE_FRACTION
    assert any("S2" in r for r in sig["reasons"])


def test_funding_window_signal_requires_cost_clear():
    hourly = fc.apr_to_hourly(0.09)
    sig = fc.funding_window_signal(_series([hourly] * 24))
    assert sig["sustained"] is False
    assert any("S4" in r for r in sig["reasons"])


# ── kill rules ───────────────────────────────────────────────────────────────
def test_kill_rules():
    assert fc.rate_flip(_series([1e-5, -1e-6])) is True
    assert fc.rate_flip(_series([1e-5, 1e-6])) is False
    # negative branch: funding turned positive -> flip (long exits).
    assert fc.rate_flip(_series([-1e-5, 1e-6]), sign=-1) is True
    assert abs(fc.basis_widen(1.005, 1.0) - 50.0) < 1e-6
    assert abs(fc.mark_oracle_basis(1.005, 1.0) - 50.0) < 1e-6
    hourly = fc.apr_to_hourly(0.03)
    assert fc.funding_decaying(_series([hourly] * 24)) is True
    hourly2 = fc.apr_to_hourly(0.10)
    assert fc.funding_decaying(_series([hourly2] * 24)) is False


# ── simulate_carry: directional stop + real-basis stop ───────────────────────
def test_simulate_carry_directional_stop_no_mark_skips():
    # Sustained positive funding but NO mark_px -> D3 skip (no episodes).
    hourly = fc.apr_to_hourly(0.30)
    funding = _series([hourly] * 60,
                      [0.0] * 60)
    eps = fc.simulate_carry(funding, basis_real=None)
    assert eps.empty


def _mark_flat(n):
    return pd.DataFrame({"time": range(n), "mark_px": [100.0] * n,
                         "oracle_px": [100.0] * n, "basis_bps": [0.0] * n})


def test_simulate_carry_directional_stop_fires():
    # Sustained funding (0.30 APR clears the cost gate) + a mark that spikes +5%
    # mid-hold -> the 2% directional hard stop must fire (regardless of funding).
    hourly = fc.apr_to_hourly(0.30)
    rates = [hourly] * 60
    times = list(range(60))
    mark = [100.0] * 30 + [105.0] * 30   # +5% adverse vs entry at t=23
    basis_real = pd.DataFrame({"time": times, "mark_px": mark,
                               "oracle_px": [100.0] * 60, "basis_bps": [0.0] * 60})
    funding = _series(rates)
    eps = fc.simulate_carry(funding, basis_real=basis_real)
    assert not eps.empty
    assert eps["execution_form"].iloc[-1] == "directional_short"
    assert "directional_stop" in eps["exit_reason"].tolist()
    stopped = eps[eps["exit_reason"] == "directional_stop"].iloc[0]
    assert abs(stopped["direction_pnl"] + stopped["risk_usd"]) < 1e-6  # -1R exactly


def test_simulate_carry_directional_stop_does_not_fire_without_move():
    # Flat mark -> no stop; hold ends on rate_flip (funding returns to 0).
    hourly = fc.apr_to_hourly(0.30)
    rates = [hourly] * 30 + [0.0] * 30
    times = list(range(60))
    basis_real = pd.DataFrame({"time": times, "mark_px": [100.0] * 60,
                               "oracle_px": [100.0] * 60, "basis_bps": [0.0] * 60})
    eps = fc.simulate_carry(_series(rates), basis_real=basis_real)
    assert not eps.empty
    assert set(eps["exit_reason"].unique()) == {"rate_flip"}


def test_simulate_carry_real_basis_kill_fires_not_premium():
    # Real mark-oracle basis widens +60bp from entry -> basis_widen fires; the
    # premium column (now ignored) stays flat -> proves the call site is re-sourced.
    hourly = fc.apr_to_hourly(0.30)
    # Enable the delta-neutral form for this test via an explicit monkeypatch of
    # the (default-off) flag, so the basis branch is exercised.
    old = fc.ENABLE_DELTA_NEUTRAL
    fc.ENABLE_DELTA_NEUTRAL = True
    try:
        spot = {"available": True, "spot_name": "UBTC"}
        rates = [hourly] * 60
        times = list(range(60))
        # basis_bps widens from 0 -> +60bp at t=30; premium stays 0 throughout.
        basis_bps = [0.0] * 30 + [60.0] * 30
        basis_real = pd.DataFrame({"time": times, "mark_px": [100.0] * 60,
                                   "oracle_px": [100.0] * 60,
                                   "basis_bps": basis_bps})
        funding = _series(rates, [0.0] * 60)
        eps = fc.simulate_carry(funding, basis_real=basis_real, spot=spot)
    finally:
        fc.ENABLE_DELTA_NEUTRAL = old
    assert not eps.empty
    assert eps["execution_form"].iloc[-1] == "delta_neutral"
    assert "basis_widen" in eps["exit_reason"].tolist()
    assert eps["basis_source"].iloc[0] == "mark_oracle"


def test_carry_g3_record_empty():
    rec = fc.carry_g3_record(pd.DataFrame())
    assert rec["n"] == 0 and rec["passed"] is False


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all funding_carry tests passed")