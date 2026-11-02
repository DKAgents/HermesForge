"""Tests for vol_vrp.py — the US-181 short-vol / VRP strategy module.

Golden-vector tests: Black-Scholes (ATM straddle ~ 0.8*S*sigma*sqrt(T)), the
held-to-expiry PnL identity, mark-to-market early exit, the vol-of-vol timing
predicate (incl. the underivable-threshold case), the MANDATORY vol-spike stop,
sizing (1R = 1% capital, MARGIN_CAP_FRAC = 1.0 = no leverage, risk_usd
re-derived when margin-capped), option execution cost, realized vol, and the
threshold-derivation routine blocked on insufficient data.
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import vol_vrp as vrp


# ── Black-Scholes (§1.3, r=0) ───────────────────────────────────────────────
def test_bs_atm_straddle_approx():
    # ATM straddle ~ 0.8 * S * sigma * sqrt(T).
    S, K, sigma, T = 100.0, 100.0, 0.30, 30 / 365.0
    premium = vrp.straddle_premium(S, K, T, sigma)
    approx = 0.8 * S * sigma * math.sqrt(T)
    assert abs(premium - approx) < 0.02 * approx, (premium, approx)


def test_bs_price_put_call_parity_atm():
    S, K, sigma, T = 100.0, 100.0, 0.25, 0.5
    c = vrp._bs_price(S, K, T, sigma, "call")
    p = vrp._bs_price(S, K, T, sigma, "put")
    # r=0 ATM: call == put.
    assert abs(c - p) < 1e-9, (c, p)


def test_bs_vega_positive():
    v = vrp._bs_vega(100.0, 100.0, 0.25, 0.30)
    assert v > 0.0


def test_bs_degenerate_zero():
    assert vrp.straddle_premium(100.0, 100.0, 0.0, 0.30) == 0.0
    assert vrp._bs_vega(0.0, 100.0, 0.25, 0.30) == 0.0


# ── PnL identity (§1.2) ─────────────────────────────────────────────────────
def test_held_to_expiry_pnl():
    # premium 10, S_T = K -> payoff 0 -> gross +10.
    r = vrp.held_to_expiry_pnl(10.0, 100.0, 100.0)
    assert abs(r["gross_pnl"] - 10.0) < 1e-9
    assert abs(r["realized_payoff"] - 0.0) < 1e-9
    # premium 10, S_T = 105 -> payoff 5 -> gross +5.
    r2 = vrp.held_to_expiry_pnl(10.0, 105.0, 100.0)
    assert abs(r2["gross_pnl"] - 5.0) < 1e-9
    # execution cost subtracts.
    r3 = vrp.held_to_expiry_pnl(10.0, 100.0, 100.0, execution_cost=1.0)
    assert abs(r3["net_pnl"] - 9.0) < 1e-9


def test_mark_to_market_early_exit():
    # IV rises -> short straddle loses (short vega). Close at higher IV.
    mtm = vrp.close_straddle_mtm(100.0, 100.0, 0.2, 0.40, premium_collected=8.0)
    assert mtm["mtm_pnl"] < 0.0


# ── Timing predicate (§2.1) ─────────────────────────────────────────────────
def test_predicate_vov_threshold_underivable():
    # No threshold -> VOV_CALM None + enter False (stay hypothesis).
    r = vrp.enter_short_vol(0.10, 40.0, 30.0, morning=True)
    assert r["vov_calm"] is None
    assert r["enter"] is False
    assert any("underivable" in x for x in r["reasons"])


def test_predicate_rich_calm_morning_enters():
    r = vrp.enter_short_vol(0.10, 40.0, 30.0, morning=True, vov_threshold=0.50)
    assert r["vov_calm"] is True
    assert r["vrp_rich"] is True
    assert r["morning"] is True
    assert r["enter"] is True


def test_predicate_not_rich_rejected():
    r = vrp.enter_short_vol(0.10, 25.0, 30.0, morning=True, vov_threshold=0.50)
    assert r["vrp_rich"] is False and r["enter"] is False


def test_predicate_not_morning_rejected():
    r = vrp.enter_short_vol(0.10, 40.0, 30.0, morning=False, vov_threshold=0.50)
    assert r["enter"] is False


def test_predicate_high_vov_rejected():
    r = vrp.enter_short_vol(0.60, 40.0, 30.0, morning=True, vov_threshold=0.50)
    assert r["vov_calm"] is False and r["enter"] is False


# ── Vol-spike stop (§3.1) ───────────────────────────────────────────────────
def test_vol_spike_no_fire_small_move():
    r = vrp.vol_spike(40.0, 40.0, 35.0, 35.0)
    assert r["triggered"] is False


def test_vol_spike_dvol_fires():
    r = vrp.vol_spike(49.0, 40.0, 35.0, 35.0)  # +22.5% DVOL
    assert r["triggered"] is True and "dvol" in r["legs"]


def test_vol_spike_iv_fires():
    r = vrp.vol_spike(40.0, 40.0, 42.0, 35.0)  # +20% IV
    assert r["triggered"] is True and "iv" in r["legs"]


# ── Sizing (§4): 1R = 1% capital, no leverage, re-derive on cap ──────────────
def test_size_risk_budget_binds_uncapped():
    # S0=100, premium=10 -> risk notional 100k (1% capital / 0.10) binds.
    sz = vrp.size_straddle(1_000_000.0, 100.0, 10.0)
    assert abs(sz["notional"] - 100_000.0) < 1e-6
    assert abs(sz["risk_usd"] - 10_000.0) < 1e-6   # exactly 1% capital
    assert sz["size_capped"] is False
    # No leverage: margin_deployed <= 1x capital.
    assert sz["margin_deployed"] <= 1_000_000.0 + 1e-6


def test_size_margin_cap_rederives_risk():
    # Huge premium -> margin rail binds; risk_usd re-derived from ACTUAL notional.
    sz = vrp.size_straddle(1_000_000.0, 100.0, 1000.0)
    assert sz["size_capped"] is True
    assert "margin cap" in sz["cap_reason"]
    assert abs(sz["risk_usd"] - sz["notional"] * 0.10) < 1e-6
    assert sz["risk_usd"] < 10_000.0   # shrunk, NOT silently labelled 1R
    assert sz["margin_deployed"] <= 1_000_000.0 + 1e-6  # still no leverage


def test_size_no_leverage_margin_cap_frac_one():
    # Quick spot-check across a few premiums: margin_deployed never exceeds capital.
    for premium in (5.0, 50.0, 500.0, 2000.0):
        sz = vrp.size_straddle(1_000_000.0, 100.0, premium,
                               margin_cap_frac=1.0)
        assert sz["margin_deployed"] <= 1_000_000.0 + 1e-6, premium


# ── Cost model (§5.2) ───────────────────────────────────────────────────────
def test_option_execution_cost_formula():
    # taker 3 + slip 1 = 4 bps * S0 * contracts * 2 legs.
    c = vrp.option_execution_cost(100.0, 100.0, taker_bps=3.0, slippage_bps=1.0)
    assert abs(c - 4.0 / 1e4 * 100.0 * 100.0 * 2.0) < 1e-9


# ── Realized vol (§2.1) ─────────────────────────────────────────────────────
def test_realized_vol_5m_flat_zero():
    assert vrp.realized_vol_5m([100.0] * 100) == 0.0
    assert vrp.realized_vol_5m([100.0]) == 0.0
    assert vrp.realized_vol_5m([]) == 0.0


def test_realized_vol_5m_positive():
    closes = [100.0 * (1.0001 ** i) for i in range(500)]
    v = vrp.realized_vol_5m(closes)
    assert v > 0.0 and math.isfinite(v)


# ── Threshold derivation (§2.2): blocked on insufficient data ───────────────
def test_derive_vov_threshold_blocked():
    r = vrp.derive_vov_threshold([])
    assert r["blocked"] is True and r["threshold"] is None


def test_derive_vov_threshold_finds_steamroller_boundary():
    # 200 records: low vol-of-vol days are profitable, high are not.
    records = []
    for i in range(200):
        vov = i / 200.0
        pnl = 1.0 if vov < 0.5 else -1.0
        records.append({"vov_level": vov, "forward_net_pnl": pnl})
    r = vrp.derive_vov_threshold(records, min_days=200)
    assert r["blocked"] is False
    assert r["threshold"] is not None
    assert 0.45 <= r["threshold"] <= 0.55   # boundary near vov=0.5


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all vol_vrp tests passed")